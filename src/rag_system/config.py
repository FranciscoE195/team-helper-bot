"""Configuration management."""

import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20


class EmbeddingModelConfig(BaseSettings):
    """Embedding model configuration."""
    model_name: str
    device: str = "cpu"
    batch_size: int = 32
    cache_dir: str | None = None


class RerankerModelConfig(BaseSettings):
    """Reranker model configuration."""
    model_name: str
    device: str = "cpu"
    batch_size: int = 16
    cache_dir: str | None = None


class LLMConfig(BaseSettings):
    """LLM configuration."""
    provider: Literal["ollama", "openai", "azure"]
    model: str
    base_url: str | None = None
    temperature: float = 0.1
    max_tokens: int = 1000


class VisionConfig(BaseSettings):
    """Vision model configuration."""
    provider: Literal["ollama", "openai", "azure"]
    model: str
    base_url: str | None = None


class ModelsConfig(BaseSettings):
    """All models configuration."""
    embedding: EmbeddingModelConfig
    reranker: RerankerModelConfig
    llm: LLMConfig
    vision: VisionConfig


class HybridSearchConfig(BaseSettings):
    """Hybrid search configuration."""
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    top_k_candidates: int = 25


class RerankConfig(BaseSettings):
    """Reranking configuration."""
    top_k: int = 10


class EvidenceConfig(BaseSettings):
    """Evidence filtering configuration."""
    min_score: float = 0.75
    insufficient_threshold: int = 2
    medium_threshold: int = 2
    high_threshold: int = 3
    max_sources: int = 5


class SearchConfig(BaseSettings):
    """Search configuration."""
    hybrid: HybridSearchConfig
    rerank: RerankConfig
    evidence: EvidenceConfig


class GitConfig(BaseSettings):
    """Git repository configuration."""
    url: str | None = None
    branch: str = "main"
    local_path: str = "/data/docs"


class MarkdownConfig(BaseSettings):
    """Markdown processing configuration."""
    extract_code_blocks: bool = True
    extract_images: bool = True


class ChunkingConfig(BaseSettings):
    """Chunking configuration."""
    strategy: Literal["section", "fixed", "semantic"] = "section"
    max_tokens: int = 512


class IngestionConfig(BaseSettings):
    """Ingestion configuration."""
    git: GitConfig
    markdown: MarkdownConfig
    chunking: ChunkingConfig
    docs_base_url: str | None = None  # Base URL for deployed documentation


class APIConfig(BaseSettings):
    """API configuration."""
    model_config = SettingsConfigDict(extra='allow')  # Allow extra fields

    cors_origins: list[str] = Field(default_factory=list)
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 60


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file: str | None = None


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(env_nested_delimiter="__", extra='allow')

    database: DatabaseConfig
    models: ModelsConfig
    search: SearchConfig
    ingestion: IngestionConfig
    api: APIConfig
    logging: LoggingConfig


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("rag_system")
    logger.setLevel(getattr(logging, config.level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper()))

    if config.format == "json":
        formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified and writable
    if config.file:
        from pathlib import Path
        log_file = Path(config.file)
        
        # Only create directory if it's writable (skip /var/log on Render)
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(config.file)
            file_handler.setLevel(getattr(logging, config.level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except PermissionError:
            # On Render, can't write to /var/log - just use console logging
            logger.warning(f"Cannot write to {config.file}, using console only")

    return logger


@lru_cache
def get_logger(name: str = "rag_system") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Load from YAML
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        config_path = Path("config/config.example.yaml")

    with Path(config_path).open() as f:
        config_dict = yaml.safe_load(f)

    # Override with environment variables
    return Settings(**config_dict)
