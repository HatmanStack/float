"""Circuit breaker pattern for external API calls in Lambda environment.

This module provides a simple circuit breaker implementation that:
- Tracks failures per Lambda container (resets on cold start)
- Automatically opens after threshold failures
- Allows test requests after recovery timeout
- Provides decorator for easy integration

The circuit breaker has three states:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests are rejected immediately
- HALF_OPEN: Testing recovery, one request allowed through

Lambda Considerations:
- State persists within a Lambda container instance
- Cold starts reset the circuit breaker (conservative behavior)
- Each Lambda instance has its own circuit breaker state
"""

import time
from enum import Enum
from functools import wraps
from typing import Callable, TypeVar

from ..exceptions import CircuitBreakerOpenError
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Simple circuit breaker for Lambda environment.

    This implementation is designed for Lambda's execution model:
    - State persists within a container for warm invocations
    - Resets on cold starts (acceptable - conservative behavior)
    - Single-threaded execution within Lambda invocation

    Example:
        >>> breaker = CircuitBreaker(name="openai", failure_threshold=3)
        >>> @with_circuit_breaker(breaker)
        ... def call_api():
        ...     return external_api.call()
        >>> call_api()  # Works normally
        >>> # After 3 failures...
        >>> call_api()  # Raises CircuitBreakerOpenError
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        name: str = "unnamed",
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit.
            recovery_timeout: Seconds before attempting recovery (half-open).
            name: Identifier for logging and error messages.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self._failures = 0
        self._last_failure_time: float | None = None
        self._state = CircuitState.CLOSED
        self._half_open_request_in_progress = False

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, transitioning to HALF_OPEN if appropriate."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and (
                time.time() - self._last_failure_time
            ) > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info(
                    "Circuit breaker transitioning to half-open",
                    extra={"data": {"name": self.name}},
                )
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failures

    def record_success(self) -> None:
        """Record successful call, resetting circuit if needed."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                "Circuit breaker closing after successful test",
                extra={"data": {"name": self.name}},
            )
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._half_open_request_in_progress = False

    def record_failure(self) -> None:
        """Record failed call, potentially opening circuit."""
        self._failures += 1
        self._last_failure_time = time.time()
        self._half_open_request_in_progress = False

        if self._failures >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                logger.warning(
                    "Circuit breaker opening",
                    extra={
                        "data": {
                            "name": self.name,
                            "failures": self._failures,
                            "threshold": self.failure_threshold,
                        }
                    },
                )
            self._state = CircuitState.OPEN

    def can_execute(self) -> bool:
        """Check if a request can be executed.

        Returns:
            True if request should proceed, False if circuit is open.
        """
        state = self.state  # May transition to HALF_OPEN

        if state == CircuitState.CLOSED:
            return True

        if state == CircuitState.HALF_OPEN:
            # Allow one test request through
            if not self._half_open_request_in_progress:
                self._half_open_request_in_progress = True
                logger.info(
                    "Circuit breaker allowing test request",
                    extra={"data": {"name": self.name}},
                )
                return True
            return False

        # OPEN state
        return False

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = None
        self._half_open_request_in_progress = False
        logger.info(
            "Circuit breaker manually reset",
            extra={"data": {"name": self.name}},
        )


def with_circuit_breaker(breaker: CircuitBreaker):
    """Decorator to wrap function with circuit breaker logic.

    Args:
        breaker: CircuitBreaker instance to use.

    Returns:
        Decorated function that checks circuit breaker before execution.

    Raises:
        CircuitBreakerOpenError: If circuit is open and rejecting requests.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            if not breaker.can_execute():
                raise CircuitBreakerOpenError(breaker.name)

            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except CircuitBreakerOpenError:
                # Don't count circuit breaker errors as failures
                raise
            except Exception:
                breaker.record_failure()
                raise

        return wrapper

    return decorator


# =============================================================================
# Module-level circuit breakers
# =============================================================================
# These persist within Lambda container for warm invocations.
# Each external service has its own circuit breaker with appropriate settings.

# OpenAI TTS - relatively reliable but can have rate limits
openai_circuit = CircuitBreaker(
    name="openai_tts",
    failure_threshold=3,
    recovery_timeout=60.0,  # 1 minute
)

# Gemini AI - can have availability issues
gemini_circuit = CircuitBreaker(
    name="gemini_ai",
    failure_threshold=3,
    recovery_timeout=60.0,  # 1 minute
)

# S3 - very reliable, higher threshold
s3_circuit = CircuitBreaker(
    name="s3_storage",
    failure_threshold=5,
    recovery_timeout=30.0,  # 30 seconds
)
