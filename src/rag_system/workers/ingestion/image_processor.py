"""Image processor worker - generates descriptions for images."""

import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from rag_system.config import get_settings
from rag_system.models.database import ImageCacheModel
from rag_system.providers.vision import get_vision_provider
from rag_system.workers.ingestion.markdown_parser import ImageData


class ImageProcessor:
    """Process images and generate descriptions."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.vision = get_vision_provider()

    def process(self, images: list[ImageData], base_path: Path) -> dict[str, str]:
        """Process images and return descriptions by hash.
        
        Args:
            images: List of image data with relative paths
            base_path: Base directory path (usually the markdown file's directory)
        """
        descriptions = {}

        for image_data in images:
            # Resolve relative image path against base_path
            if Path(image_data.path).is_absolute():
                image_path = Path(image_data.path)
            else:
                image_path = (base_path / image_data.path).resolve()

            if not image_path.exists():
                continue

            # Calculate image hash
            image_hash = self._hash_file(image_path)

            # Check cache
            cached = self.db.query(ImageCacheModel).filter(
                ImageCacheModel.image_hash == image_hash
            ).first()

            if cached:
                descriptions[image_hash] = cached.description
            else:
                # Generate description
                description = self.vision.describe_image(str(image_path))

                # Cache it
                cache_entry = ImageCacheModel(
                    image_hash=image_hash,
                    description=description,
                    model_version=self.settings.models.vision.model,
                )
                self.db.add(cache_entry)
                self.db.commit()

                descriptions[image_hash] = description

        return descriptions

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with Path(file_path).open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
