"""Webhook endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from rag_system.api.dependencies import get_ingestion_service
from rag_system.config import get_logger
from rag_system.exceptions import IngestionError
from rag_system.models.api import IngestionResponse
from rag_system.services.ingestion_service import IngestionService

router = APIRouter()
logger = get_logger(__name__)


# TODO: Re-enable Git webhook for automated updates
# @router.post("/git", response_model=IngestionResponse)
# async def git_webhook(
#     request: WebhookGitRequest,
#     background_tasks: BackgroundTasks,
#     service: Annotated[IngestionService, Depends(get_ingestion_service)],
# ) -> IngestionResponse:
#     """Handle Git webhook for documentation updates."""
#     logger.info(
#         "Received Git webhook",
#         extra={
#             "event": request.event,
#             "repository": request.repository,
#             "branch": request.branch,
#             "changed_files": len(request.changed_files),
#         },
#     )
#
#     try:
#         result = service.ingest_files(request.changed_files)
#         logger.info(
#             "Ingestion completed successfully",
#             extra={
#                 "processed_files": result.processed_files,
#                 "duration_seconds": result.duration_seconds,
#             },
#         )
#         return result
#
#     except IngestionError as e:
#         logger.error(f"Ingestion error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
#
#     except Exception as e:
#         logger.error(f"Unexpected error in ingestion: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.post("/ingest-all", response_model=IngestionResponse)
async def ingest_all_documents(
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestionResponse:
    """Manually trigger ingestion of all documents in the configured directory."""
    logger.info("Manual ingestion triggered for all documents")

    try:
        result = service.ingest_files(changed_files=None)
        logger.info(
            "Ingestion completed successfully",
            extra={
                "processed_files": result.processed_files,
                "duration_seconds": result.duration_seconds,
            },
        )
        return result

    except IngestionError as e:
        logger.error(f"Ingestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e

    except Exception as e:
        logger.error(f"Unexpected error in ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e
