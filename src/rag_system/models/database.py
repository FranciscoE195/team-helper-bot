"""Database ORM models."""

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Boolean, Float, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class DocumentModel(Base):
    """Document table."""
    __tablename__ = "documents"

    doc_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    breadcrumb: Mapped[list[str]] = mapped_column(ARRAY(Text))
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    sections: Mapped[list["DocumentSectionModel"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentSectionModel(Base):
    """Document section table."""
    __tablename__ = "document_sections"

    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    doc_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))  # multilingual-e5-large
    content_tsv: Mapped[str | None] = mapped_column(TSVECTOR)
    section_order: Mapped[int | None] = mapped_column(Integer)
    has_code: Mapped[bool] = mapped_column(Boolean, default=False)
    has_images: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    document: Mapped["DocumentModel"] = relationship(back_populates="sections")
    images: Mapped[list["DocumentImageModel"]] = relationship(back_populates="section", cascade="all, delete-orphan")


class ImageCacheModel(Base):
    """Image cache table."""
    __tablename__ = "image_cache"

    image_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class DocumentImageModel(Base):
    """Document image table."""
    __tablename__ = "document_images"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_sections.section_id", ondelete="CASCADE"), nullable=False)
    image_hash: Mapped[str] = mapped_column(Text, ForeignKey("image_cache.image_hash"), nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    section: Mapped["DocumentSectionModel"] = relationship(back_populates="images")


class QueryTraceModel(Base):
    """Query trace table."""
    __tablename__ = "query_traces"

    trace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(Text)
    reranker_model: Mapped[str | None] = mapped_column(Text)
    llm_model: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

    citations: Mapped[list["TraceCitationModel"]] = relationship(back_populates="trace", cascade="all, delete-orphan")
    answers: Mapped[list["TraceAnswerModel"]] = relationship(back_populates="trace", cascade="all, delete-orphan")


class TraceCitationModel(Base):
    """Trace citation table."""
    __tablename__ = "trace_citations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    trace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("query_traces.trace_id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_sections.section_id"), nullable=False)
    citation_number: Mapped[int] = mapped_column(Integer, nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    doc_title: Mapped[str | None] = mapped_column(Text)
    section_title: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)

    trace: Mapped["QueryTraceModel"] = relationship(back_populates="citations")


class TraceAnswerModel(Base):
    """Trace answer table."""
    __tablename__ = "trace_answers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    trace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("query_traces.trace_id", ondelete="CASCADE"), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer)
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    trace: Mapped["QueryTraceModel"] = relationship(back_populates="answers")


class TraceSectionSnapshotModel(Base):
    """Trace section snapshot table."""
    __tablename__ = "trace_section_snapshots"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    trace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("query_traces.trace_id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_sections.section_id"), nullable=False)
    content_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
