"""Database writer worker - writes documents and sections to database."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from rag_system.models.database import (
    DocumentImageModel,
    DocumentModel,
    DocumentSectionModel,
)
from rag_system.workers.ingestion.markdown_parser import DocumentData


@dataclass
class WriteResult:
    """Result of database write operation."""
    updated: int
    added: int
    deleted: int


class DatabaseWriter:
    """Write documents and sections to database."""

    def __init__(self, db: Session):
        self.db = db

    def write(self, document: DocumentData) -> WriteResult:
        """Write document to database."""
        result = WriteResult(updated=0, added=0, deleted=0)

        # Check if document exists
        existing_doc = self.db.query(DocumentModel).filter(
            DocumentModel.file_path == document.file_path
        ).first()

        if existing_doc:
            # Check if content changed
            if existing_doc.content_hash != document.content_hash:
                result = self._update_document(existing_doc, document)
            # else: no changes, skip
        else:
            # New document
            result = self._create_document(document)

        self.db.commit()
        return result

    def _create_document(self, document: DocumentData) -> WriteResult:
        """Create new document and sections."""
        # Create document
        doc_model = DocumentModel(
            title=document.title,
            url=document.url,
            file_path=document.file_path,
            breadcrumb=document.breadcrumb,
            content_hash=document.content_hash,
        )
        self.db.add(doc_model)
        self.db.flush()  # Get doc_id

        # Create sections
        for section in document.sections:
            section_model = DocumentSectionModel(
                doc_id=doc_model.doc_id,
                title=section.title,
                content=section.content,
                embedding=section.embedding if hasattr(section, 'embedding') else None,
                section_order=section.order,
                has_code=section.has_code,
                has_images=section.has_images,
            )
            self.db.add(section_model)
            self.db.flush()

            # Add images
            if section.has_images:
                self._add_images(section_model.section_id, section.images, document.image_descriptions)

        return WriteResult(updated=0, added=len(document.sections), deleted=0)

    def _update_document(self, existing_doc: DocumentModel, document: DocumentData) -> WriteResult:
        """Update existing document."""
        # Update document metadata
        existing_doc.title = document.title
        existing_doc.url = document.url
        existing_doc.breadcrumb = document.breadcrumb
        existing_doc.content_hash = document.content_hash

        # Delete old sections
        old_sections = self.db.query(DocumentSectionModel).filter(
            DocumentSectionModel.doc_id == existing_doc.doc_id
        ).all()

        for section in old_sections:
            self.db.delete(section)

        deleted_count = len(old_sections)

        # Add new sections
        for section in document.sections:
            section_model = DocumentSectionModel(
                doc_id=existing_doc.doc_id,
                title=section.title,
                content=section.content,
                embedding=section.embedding if hasattr(section, 'embedding') else None,
                section_order=section.order,
                has_code=section.has_code,
                has_images=section.has_images,
            )
            self.db.add(section_model)
            self.db.flush()

            # Add images
            if section.has_images:
                self._add_images(section_model.section_id, section.images, document.image_descriptions)

        return WriteResult(updated=len(document.sections), added=0, deleted=deleted_count)

    def _add_images(
        self,
        section_id: UUID,
        images: list,
        descriptions: dict[str, str],
    ) -> None:
        """Add image references to section."""
        for image_data in images:
            # Calculate hash (should match ImageProcessor)
            import hashlib
            from pathlib import Path
            image_path = Path(image_data.path)

            if not image_path.exists():
                continue

            with Path(image_path).open('rb') as f:
                image_hash = hashlib.sha256(f.read()).hexdigest()

            image_model = DocumentImageModel(
                section_id=section_id,
                image_hash=image_hash,
                image_path=image_data.path,
                alt_text=image_data.alt_text,
            )
            self.db.add(image_model)
