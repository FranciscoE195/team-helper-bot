"""Embedder worker - generates embeddings for document sections."""

from rag_system.providers.embedder import get_embedder_provider
from rag_system.workers.ingestion.markdown_parser import DocumentData


class EmbedderWorker:
    """Generate embeddings for document sections."""

    def __init__(self):
        self.embedder = get_embedder_provider()

    def embed_document(self, document: DocumentData) -> DocumentData:
        """Add embeddings to all sections in document."""
        # Prepare texts for embedding
        texts = []
        for section in document.sections:
            # Combine title and content for better context
            text = section.title or ""
            if text:
                text += "\n\n"
            text += section.content
            texts.append(text)

        # Generate embeddings in batch
        embeddings = self.embedder.embed_batch(texts)

        # Attach embeddings to sections
        for section, embedding in zip(document.sections, embeddings):
            section.embedding = embedding

        return document
