"""Ingestion service - orchestrates document ingestion."""

import time

from codetiming import Timer
from sqlalchemy.orm import Session

from rag_system.config import get_logger
from rag_system.models.api import IngestionResponse
from rag_system.workers.ingestion.database_writer import DatabaseWriter
from rag_system.providers.embedder import get_embedder_provider
from rag_system.workers.ingestion.git_fetcher import GitFetcher
from rag_system.workers.ingestion.image_processor import ImageProcessor
from rag_system.workers.ingestion.markdown_parser import MarkdownParser

logger = get_logger(__name__)


class IngestionService:
    """Ingestion service orchestrating the ingestion pipeline."""

    def __init__(self, db: Session):
        self.db = db

        # Initialize workers
        self.git_fetcher = GitFetcher()
        self.parser = MarkdownParser()
        self.image_processor = ImageProcessor(db)
        self.embedder = get_embedder_provider()
        self.writer = DatabaseWriter(db)

    @Timer(name="ingestion_pipeline", text="Ingestion pipeline completed in {:.2f}s", logger=logger.info)
    def ingest_files(self, changed_files: list[str] | None = None) -> IngestionResponse:
        """Ingest files from local directory.
        
        Args:
            changed_files: Optional list of specific files to process.
                          If None, processes all markdown files in the directory.
        """
        start_time = time.time()

        logger.info(
            "Starting ingestion pipeline",
            extra={"changed_files_count": len(changed_files) if changed_files else "all"},
        )

        stats = {
            "processed_files": 0,
            "updated_sections": 0,
            "added_sections": 0,
            "deleted_sections": 0,
        }

        # Step 1: Fetch files from local directory
        logger.debug("Step 1: Fetching files from local directory")
        with Timer(name="directory_scan", text="Directory scan: {:.3f}s", logger=logger.debug):
            local_files = self.git_fetcher.fetch(changed_files)
        stats["processed_files"] = len(local_files)
        logger.info(f"Found {len(local_files)} files to process")

        # Step 2: Process each file
        for idx, file_path in enumerate(local_files, 1):
            logger.info(f"Processing file {idx}/{len(local_files)}: {file_path}")

            # Parse markdown
            logger.debug(f"Parsing markdown: {file_path}")
            with Timer(name="markdown_parse", text="Markdown parse: {:.3f}s", logger=logger.debug):
                document_data = self.parser.parse(file_path)
            logger.debug(f"Parsed {len(document_data.sections)} sections")

            # Process images
            if document_data.images:
                logger.debug(f"Processing {len(document_data.images)} images")
                with Timer(name="image_process", text="Image processing: {:.3f}s", logger=logger.debug):
                    # Pass the directory of the markdown file as base_path
                    base_path = file_path.parent
                    image_descriptions = self.image_processor.process(document_data.images, base_path)
                document_data.image_descriptions = image_descriptions
                logger.debug(f"Generated {len(image_descriptions)} image descriptions")

            # Generate embeddings
            logger.debug("Generating embeddings")
            with Timer(name="embedding_generation", text="Embedding generation: {:.3f}s", logger=logger.debug):
                # Adaptação: embed_document não existe mais, então implementa aqui
                # Prepara textos para embedding
                texts = []
                for section in document_data.sections:
                    text = section.title or ""
                    if text:
                        text += "\n\n"
                    text += section.content
                    texts.append(text)

                embeddings = self.embedder.embed_batch(texts)
                for section, embedding in zip(document_data.sections, embeddings):
                    section.embedding = embedding

            # Write to database
            logger.debug("Writing to database")
            with Timer(name="db_write", text="Database write: {:.3f}s", logger=logger.debug):
                result = self.writer.write(document_data)

            stats["updated_sections"] += result.updated
            stats["added_sections"] += result.added
            stats["deleted_sections"] += result.deleted

            logger.info(
                f"File processed: {file_path}",
                extra={
                    "updated": result.updated,
                    "added": result.added,
                    "deleted": result.deleted,
                },
            )

        duration = time.time() - start_time

        logger.info(
            "Ingestion pipeline completed",
            extra={
                "processed_files": stats["processed_files"],
                "updated_sections": stats["updated_sections"],
                "added_sections": stats["added_sections"],
                "deleted_sections": stats["deleted_sections"],
                "duration_seconds": round(duration, 2),
            },
        )

        return IngestionResponse(
            success=True,
            message=f"Ingested {stats['processed_files']} files successfully",
            processed_files=stats["processed_files"],
            updated_sections=stats["updated_sections"],
            added_sections=stats["added_sections"],
            deleted_sections=stats["deleted_sections"],
            duration_seconds=round(duration, 2),
        )
