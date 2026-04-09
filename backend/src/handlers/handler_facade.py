"""Delegation mixin for :class:`LambdaHandler`.

Phase 4 revision (iteration 2) moves the legacy delegation methods and
the ``handle_request`` entry point out of :mod:`lambda_handler` so that
module can become a thin shim owning only service construction.

The class in :mod:`lambda_handler` inherits from
:class:`LambdaHandlerFacade` and the delegations reach its concrete
attributes (``self.summary``, ``self.meditation``, ``self.jobs``) via
standard attribute lookup.
"""

from typing import Any, Dict, List, Optional, Union

from ..models.requests import MeditationRequestModel, SummaryRequestModel, parse_request_body
from ..utils.logging_utils import get_logger
from .middleware import (
    apply_middleware,
    cors_middleware,
    create_error_response,
    create_success_response,
    error_handling_middleware,
    json_middleware,
    method_validation_middleware,
    request_size_validation_middleware,
)

logger = get_logger(__name__)


class LambdaHandlerFacade:
    """Delegation surface that back-compat tests exercise.

    Concrete subclasses MUST populate ``self.summary``, ``self.meditation``,
    and ``self.jobs`` in ``__init__``. Every method here is a thin
    delegation into one of those three.
    """

    summary: Any
    meditation: Any
    jobs: Any

    def get_tts_provider(self) -> Any:
        return self.meditation.get_tts_provider()

    def handle_summary_request(self, request: SummaryRequestModel) -> Dict[str, Any]:
        return self.summary.handle(request)

    def handle_meditation_request(self, request: MeditationRequestModel) -> Dict[str, Any]:
        return self.meditation.handle(request)

    def process_meditation_async(self, job_id: str, request_dict: Dict[str, Any]) -> None:
        self.meditation.process_async(job_id, request_dict)

    def handle_job_status(self, user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.handle_status(user_id, job_id)

    def handle_download_request(
        self,
        user_id: str,
        job_id: str,
        job_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        return self.jobs.handle_download(user_id, job_id, job_data)

    def _ensure_input_data_is_dict(
        self, input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        return self.meditation._ensure_input_data_is_dict(input_data)

    def _generate_meditation_audio(self, meditation_text: str, timestamp: str) -> tuple[str, str]:
        return self.meditation._generate_meditation_audio(meditation_text, timestamp)

    def _invoke_async_meditation(self, request: MeditationRequestModel, job_id: str) -> None:
        self.meditation._invoke_async_meditation(request, job_id)

    def _process_meditation_base64(self, job_id: str, request: MeditationRequestModel) -> None:
        self.meditation._process_base64(job_id, request)

    def _process_meditation_hls(self, job_id: str, request: MeditationRequestModel) -> None:
        self.meditation._process_hls(job_id, request)

    def _mark_job_failed(
        self,
        request: MeditationRequestModel,
        job_id: str,
        error: BaseException,
        attempts: int,
    ) -> None:
        self.meditation._mark_job_failed(request, job_id, error, attempts)

    def _store_summary_results(
        self, request: SummaryRequestModel, response: Any, has_audio: bool
    ) -> None:
        self.summary._store_summary_results(request, response, has_audio)

    def _store_meditation_results(self, request: MeditationRequestModel, response: Any) -> None:
        self.meditation._store_meditation_results(request, response)

    @apply_middleware(
        cors_middleware,
        json_middleware,
        method_validation_middleware(["POST"]),
        request_size_validation_middleware,
        error_handling_middleware,
    )
    def handle_request(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Exceptions propagate directly to ``error_handling_middleware`` which
        # logs and converts them. A redundant try/except here would double-log.
        parsed_body = event.get("parsed_body", {})
        request = parse_request_body(parsed_body)
        if isinstance(request, SummaryRequestModel):
            result = self.handle_summary_request(request)
        elif isinstance(request, MeditationRequestModel):
            result = self.handle_meditation_request(request)
        else:
            from ..config.constants import HTTP_BAD_REQUEST

            return create_error_response(HTTP_BAD_REQUEST, "Unsupported request type")
        return create_success_response(result)
