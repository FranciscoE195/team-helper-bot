"""Markdown parser worker - parses markdown files into structured data."""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from rag_system.config import get_settings


@dataclass
class ImageData:
    """Image data from markdown."""
    path: str
    alt_text: str | None


@dataclass
class SectionData:
    """Section data from markdown."""
    title: str | None
    content: str
    order: int
    has_code: bool
    has_images: bool
    images: list[ImageData] = field(default_factory=list)


@dataclass
class DocumentData:
    """Complete document data."""
    file_path: str
    title: str
    url: str | None
    breadcrumb: list[str]
    content_hash: str
    sections: list[SectionData]
    images: list[ImageData] = field(default_factory=list)
    image_descriptions: dict[str, str] = field(default_factory=dict)


class MarkdownParser:
    """Parse markdown files into structured data."""

    def parse(self, file_path: Path) -> DocumentData:
        """Parse markdown file."""
        with Path(file_path).open('r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata
        title = self._extract_title(content)
        breadcrumb = self._build_breadcrumb(file_path)
        url = self._build_url(file_path)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Parse sections
        sections = self._parse_sections(content)

        # Collect all images
        all_images = []
        for section in sections:
            all_images.extend(section.images)

        return DocumentData(
            file_path=str(file_path),
            title=title,
            url=url,
            breadcrumb=breadcrumb,
            content_hash=content_hash,
            sections=sections,
            images=all_images,
        )

    def _extract_title(self, content: str) -> str:
        """Extract document title from first H1 (markdown or HTML)."""
        # Try markdown H1
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Try HTML H1
        match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        if match:
            # Strip HTML tags from title
            title = re.sub(r'<[^>]+>', '', match.group(1))
            return title.strip()
        
        return "Untitled"

    def _build_breadcrumb(self, file_path: Path) -> list[str]:
        """Build breadcrumb from file path."""
        parts = file_path.relative_to(file_path.parent.parent).parts
        return list(parts[:-1])  # Exclude filename

    def _build_url(self, file_path: Path) -> str | None:
        """Build documentation URL from file path."""
        settings = get_settings()
        base_url = settings.ingestion.docs_base_url
        
        if not base_url:
            return None
        
        # Get local path from settings
        local_path = Path(settings.ingestion.git.local_path)
        
        try:
            # Get relative path from local_path
            rel_path = file_path.relative_to(local_path)
            
            # Convert to HTML path (change .md to .html)
            html_path = str(rel_path).replace('\\', '/').replace('.md', '.html')
            
            # Build full URL
            return f"{base_url}/{html_path}"
        except ValueError:
            # file_path is not relative to local_path
            return None

    def _parse_sections(self, content: str) -> list[SectionData]:
        """Parse content into sections by headers (markdown and HTML)."""
        sections = []

        # Convert HTML headers to markdown for consistent splitting
        content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', content, flags=re.IGNORECASE | re.DOTALL)

        # Split by H2 and H3 headers (both become sections)
        pattern = r'^(##|###)\s+(.+)$'
        parts = re.split(pattern, content, flags=re.MULTILINE)

        # First part is before any H2/H3 (intro)
        if parts[0].strip():
            sections.append(self._create_section(None, parts[0], 0))

        # Process header sections (pattern captures: header_level, title, content)
        section_order = 1
        for i in range(1, len(parts), 3):
            if i + 2 < len(parts):
                header_level = parts[i]  # ## or ###
                title = parts[i + 1].strip()
                section_content = parts[i + 2]
                sections.append(self._create_section(title, section_content, section_order))
                section_order += 1

        return sections

    def _create_section(self, title: str | None, content: str, order: int) -> SectionData:
        """Create section data."""
        # Check for code blocks
        has_code = '```' in content or '    ' in content

        # Extract images
        images = self._extract_images(content)
        has_images = len(images) > 0

        return SectionData(
            title=title,
            content=content.strip(),
            order=order,
            has_code=has_code,
            has_images=has_images,
            images=images,
        )

    def _extract_images(self, content: str) -> list[ImageData]:
        """Extract images from markdown and HTML."""
        images = []
        
        # Markdown syntax: ![alt](path)
        md_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        for match in re.finditer(md_pattern, content):
            alt_text = match.group(1) or None
            image_path = match.group(2)
            images.append(ImageData(path=image_path, alt_text=alt_text))

        # HTML syntax: <img src="path" alt="text">
        html_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
        for match in re.finditer(html_pattern, content, re.IGNORECASE):
            image_path = match.group(1)
            alt_text = match.group(2) or None
            images.append(ImageData(path=image_path, alt_text=alt_text))

        return images
