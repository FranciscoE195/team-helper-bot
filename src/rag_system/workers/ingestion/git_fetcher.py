"""Directory fetcher worker - fetches files from a local directory.

Note: Git webhook integration is disabled for now but can be re-enabled later.
To re-enable: uncomment the Git-related methods and import git library.
"""

from pathlib import Path

# import git  # TODO: Re-enable for Git webhook support
from rag_system.config import get_logger, get_settings
from rag_system.exceptions import IngestionError

logger = get_logger(__name__)


class GitFetcher:
    """Fetch files from a local directory (Git integration disabled for now)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.git_config = self.settings.ingestion.git
        self.local_path = Path(self.git_config.local_path)

    def fetch(self, changed_files: list[str] | None = None) -> list[Path]:
        """Fetch markdown files from local directory.
        
        Args:
            changed_files: Optional list of specific files to process.
                          If None, scans entire directory for all .md files.
        """
        try:
            # Ensure directory exists
            if not self.local_path.exists():
                raise IngestionError(
                    f"Local path does not exist: {self.local_path}. "
                    f"Please create the directory and add your markdown files."
                )

            logger.info(f"Using local directory: {self.local_path}")

            # If no specific files provided, scan entire directory
            if not changed_files:
                logger.info("Scanning directory for all markdown files...")
                file_paths = list(self.local_path.rglob("*.md"))
                logger.info(f"Found {len(file_paths)} markdown files in directory")
                return file_paths

            # Process specific files
            file_paths = []
            for file_path in changed_files:
                if file_path.endswith('.md'):
                    full_path = self.local_path / file_path
                    if full_path.exists():
                        file_paths.append(full_path)
                    else:
                        logger.warning(f"File not found: {full_path}")

            logger.info(f"Found {len(file_paths)} markdown files to process")
            return file_paths

        except Exception as e:
            logger.error(f"Failed to fetch files: {e}", exc_info=True)
            raise IngestionError(f"Failed to fetch files: {e}") from e

    # TODO: Re-enable these methods for Git webhook support
    # def _clone_repo(self) -> None:
    #     """Clone repository."""
    #     logger.info(f"Cloning from {self.git_config.url}")
    #     self.local_path.parent.mkdir(parents=True, exist_ok=True)
    #     git.Repo.clone_from(
    #         self.git_config.url,
    #         self.local_path,
    #         branch=self.git_config.branch,
    #     )
    #     logger.info("Repository cloned successfully")
    #
    # def _pull_repo(self) -> None:
    #     """Pull latest changes."""
    #     logger.info("Pulling latest changes")
    #     repo = git.Repo(self.local_path)
    #     origin = repo.remotes.origin
    #     origin.pull(self.git_config.branch)
    #     logger.info("Repository updated successfully")
