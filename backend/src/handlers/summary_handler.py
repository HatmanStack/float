"""Summary request handler.

Extracted from :mod:`lambda_handler` as part of Phase 4 Task 1 of the
2026-04-08-audit-float plan. Owns the `/` (POST) summary pathway and its
S3 persistence helper.
"""

from datetime import datetime, timezone
from typing import Any, Dict  # noqa: I001

from ..config.settings import settings
from ..models.requests import SummaryRequestModel
from ..models.responses import create_summary_response
from ..services.ai_service import AIService
from ..services.s3_storage_service import S3StorageService
from ..utils.audio_utils import cleanup_temp_file, decode_audio_base64
from ..utils.file_utils import generate_request_id
from ..utils.logging_utils import get_logger
from .routes import _mask_id

logger = get_logger(__name__)


class SummaryHandler:
    """Handle summary/sentiment-analysis requests."""

    def __init__(self, parent: Any) -> None:
        self._parent = parent

    @property
    def ai_service(self) -> AIService:
        return self._parent.ai_service

    @property
    def storage_service(self) -> S3StorageService:
        return self._parent.storage_service

    def handle(self, request: SummaryRequestModel) -> Dict[str, Any]:
        logger.info(
            "Processing summary request",
            extra={"data": {"user_id": _mask_id(request.user_id)}},
        )
        audio_file = None
        has_audio = bool(request.audio) and request.audio != "NotAvailable"
        if has_audio:
            audio_file = decode_audio_base64(request.audio)
        # Normalize the "NotAvailable" sentinel to None so downstream
        # AI prompt construction never embeds the literal string.
        user_text = request.prompt if request.prompt and request.prompt != "NotAvailable" else None
        try:
            summary_result = self.ai_service.analyze_sentiment(
                audio_file=audio_file, user_text=user_text
            )
            request_id = generate_request_id()
            response = create_summary_response(request_id, request.user_id, summary_result)
            self._store_summary_results(request, response, has_audio)
            return response.to_dict()
        finally:
            if audio_file:
                cleanup_temp_file(audio_file)

    def _store_summary_results(
        self, request: SummaryRequestModel, response: Any, has_audio: bool
    ) -> None:
        # Microsecond UTC + request_id avoids collisions for concurrent
        # summary requests from the same user.
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        request_id = response.request_id
        object_key = f"{request.user_id}/summary/{timestamp}-{request_id}.json"
        self.storage_service.upload_json(
            bucket=settings.AWS_S3_BUCKET, key=object_key, data=response.to_dict()
        )
        if has_audio:
            audio_data = {
                "user_audio": request.audio,
                "user_id": request.user_id,
                "request_id": request_id,
            }
            audio_key = f"{request.user_id}/audio/{timestamp}-{request_id}.json"
            self.storage_service.upload_json(
                bucket=settings.AWS_S3_BUCKET, key=audio_key, data=audio_data
            )
