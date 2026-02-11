"""Hybrid search worker - combines vector and keyword search."""

from codetiming import Timer
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from rag_system.config import get_logger, get_settings
from rag_system.models.database import DocumentModel, DocumentSectionModel
from rag_system.models.domain import SearchResult, Section
from rag_system.providers.embedder import get_embedder_provider

logger = get_logger(__name__)


class HybridSearcher:
    """Hybrid search combining vector similarity and keyword matching."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.embedder = get_embedder_provider()
        self.config = self.settings.search.hybrid

    @Timer(name="hybrid_search_full", text="Hybrid search: {:.3f}s", logger=None)
    def search(self, query: str) -> list[SearchResult]:
        """Perform hybrid search."""
        logger.debug(f"Performing hybrid search for: {query[:50]}...")

        # Step 1: Embed query
        with Timer(name="query_embedding", text="Query embedding: {:.3f}s", logger=logger.debug):
            query_embedding = self.embedder.embed(query)

        # Step 2: Vector search
        with Timer(name="vector_search", text="Vector search: {:.3f}s", logger=logger.debug):
            vector_results = self._vector_search(query_embedding)
        logger.debug(f"Vector search found {len(vector_results)} results")

        # Step 3: Keyword search
        with Timer(name="keyword_search", text="Keyword search: {:.3f}s", logger=logger.debug):
            keyword_results = self._keyword_search(query)
        logger.debug(f"Keyword search found {len(keyword_results)} results")

        # Step 4: Merge and score
        merged_results = self._merge_results(vector_results, keyword_results)
        logger.debug(f"Merged to {len(merged_results)} unique results")

        return merged_results

    def _vector_search(self, query_embedding: list[float]) -> dict[str, tuple[Section, float]]:
        """Perform vector similarity search."""
        results = (
            self.db.query(
                DocumentSectionModel,
                DocumentModel,
                DocumentSectionModel.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .join(DocumentModel, DocumentSectionModel.doc_id == DocumentModel.doc_id)
            .filter(DocumentSectionModel.embedding.isnot(None))
            .order_by(text("distance"))
            .limit(self.config.top_k_candidates)
            .all()
        )

        vector_dict = {}
        for section_model, doc_model, distance in results:
            section = self._model_to_section(section_model, doc_model)
            score = 1.0 - distance  # Convert distance to similarity
            vector_dict[str(section.section_id)] = (section, score)

        return vector_dict

    def _keyword_search(self, query: str) -> dict[str, tuple[Section, float]]:
        """Perform keyword search using PostgreSQL full-text search."""
        # Create tsquery from search terms
        tsquery = func.plainto_tsquery("english", query)

        results = (
            self.db.query(
                DocumentSectionModel,
                DocumentModel,
                func.ts_rank(DocumentSectionModel.content_tsv, tsquery).label("rank"),
            )
            .join(DocumentModel, DocumentSectionModel.doc_id == DocumentModel.doc_id)
            .filter(DocumentSectionModel.content_tsv.op("@@")(tsquery))
            .order_by(text("rank DESC"))
            .limit(self.config.top_k_candidates)
            .all()
        )

        keyword_dict = {}
        for section_model, doc_model, rank in results:
            section = self._model_to_section(section_model, doc_model)
            keyword_dict[str(section.section_id)] = (section, float(rank))

        return keyword_dict

    def _merge_results(
        self,
        vector_results: dict[str, tuple[Section, float]],
        keyword_results: dict[str, tuple[Section, float]],
    ) -> list[SearchResult]:
        """Merge vector and keyword results with weighted scoring."""
        merged = {}
        all_section_ids = set(vector_results.keys()) | set(keyword_results.keys())

        for section_id in all_section_ids:
            vector_data = vector_results.get(section_id, (None, 0.0))
            keyword_data = keyword_results.get(section_id, (None, 0.0))

            # Get section (prefer vector result if both exist)
            section = vector_data[0] or keyword_data[0]

            # Normalize scores
            vector_score = vector_data[1]
            keyword_score = keyword_data[1]

            # Weighted combination
            combined_score = (
                self.config.vector_weight * vector_score +
                self.config.keyword_weight * keyword_score
            )

            merged[section_id] = SearchResult(
                section=section,
                vector_score=vector_score,
                keyword_score=keyword_score,
                combined_score=combined_score,
            )

        # Sort by combined score
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x.combined_score,
            reverse=True,
        )

        return sorted_results

    def _model_to_section(
        self,
        section_model: DocumentSectionModel,
        doc_model: DocumentModel,
    ) -> Section:
        """Convert database model to domain model."""
        return Section(
            section_id=str(section_model.section_id),
            doc_id=str(section_model.doc_id),
            title=section_model.title,
            content=section_model.content,
            embedding=section_model.embedding,
            doc_title=doc_model.title,
            url=doc_model.url,
            breadcrumb=doc_model.breadcrumb or [],
            has_code=section_model.has_code,
            has_images=section_model.has_images,
        )
