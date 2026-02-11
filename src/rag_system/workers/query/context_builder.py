"""Context builder worker - formats evidence for LLM prompt."""

from sqlalchemy.orm import Session

from rag_system.models.database import DocumentImageModel, ImageCacheModel
from rag_system.models.domain import Evidence


class ContextBuilder:
    """Build context string from evidence for LLM."""

    def __init__(self, db: Session):
        self.db = db

    def build(self, evidence: list[Evidence]) -> str:
        """Build formatted context from evidence."""
        context_parts = []

        for ev in evidence:
            section = ev.section

            # Build source header with citation number
            header = f"[{ev.citation_number}]\n"
            header += f"Document: {section.doc_title}\n"

            if section.title:
                header += f"Section: {section.title}\n"

            if section.breadcrumb:
                breadcrumb_str = " > ".join(section.breadcrumb)
                header += f"Path: {breadcrumb_str}\n"

            context_parts.append(header)

            # Add image descriptions if present
            if section.has_images:
                images = self._get_image_descriptions(section.section_id)
                if images:
                    context_parts.append("\n[Images in this section]")
                    for img_desc in images:
                        context_parts.append(f"- {img_desc}")
                    context_parts.append("")

            # Add content
            context_parts.append(f"Content:\n{section.content}\n")
            context_parts.append("-" * 80 + "\n")

        return "\n".join(context_parts)

    def _get_image_descriptions(self, section_id: str) -> list[str]:
        """Get image descriptions for a section."""
        results = (
            self.db.query(ImageCacheModel.description)
            .join(DocumentImageModel, DocumentImageModel.image_hash == ImageCacheModel.image_hash)
            .filter(DocumentImageModel.section_id == section_id)
            .all()
        )

        return [desc[0] for desc in results]
