"""Unit tests for the circuit breaker implementation."""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.exceptions import CircuitBreakerOpenError
from src.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    with_circuit_breaker,
    gemini_circuit,
    openai_circuit,
    s3_circuit,
)


@pytest.mark.unit
class TestCircuitState:
    """Test CircuitState enum."""

    def test_states_exist(self):
        """Verify all states are defined."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


@pytest.mark.unit
class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_initial_state_is_closed(self):
        """New circuit breaker should be in closed state."""
        breaker = CircuitBreaker(name="test")
        assert breaker.state == CircuitState.CLOSED

    def test_can_execute_when_closed(self):
        """Should allow execution when closed."""
        breaker = CircuitBreaker(name="test")
        assert breaker.can_execute() is True

    def test_records_success(self):
        """Recording success should reset failure count."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        breaker._failures = 2
        breaker.record_success()
        assert breaker.failure_count == 0

    def test_records_failure(self):
        """Recording failure should increment count."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        breaker.record_failure()
        assert breaker.failure_count == 1

    def test_opens_after_threshold_failures(self):
        """Circuit should open after threshold failures."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    def test_rejects_when_open(self):
        """Should reject execution when open."""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        breaker.record_failure()  # Opens the circuit

        assert breaker.state == CircuitState.OPEN
        assert breaker.can_execute() is False

    def test_transitions_to_half_open_after_timeout(self):
        """Circuit should transition to half-open after recovery timeout."""
        breaker = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)
        breaker.record_failure()  # Opens the circuit

        assert breaker.state == CircuitState.OPEN

        time.sleep(0.15)  # Wait for recovery timeout

        assert breaker.state == CircuitState.HALF_OPEN

    def test_allows_one_request_in_half_open(self):
        """Should allow one test request in half-open state."""
        breaker = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)
        breaker.record_failure()
        time.sleep(0.15)

        assert breaker.can_execute() is True  # First request allowed
        assert breaker.can_execute() is False  # Second request blocked

    def test_closes_after_success_in_half_open(self):
        """Circuit should close after successful request in half-open."""
        breaker = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)
        breaker.record_failure()
        time.sleep(0.15)

        breaker.can_execute()  # Consume the test request
        breaker.record_success()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_reopens_after_failure_in_half_open(self):
        """Circuit should reopen after failure in half-open."""
        breaker = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)
        breaker.record_failure()
        time.sleep(0.15)

        breaker.can_execute()  # Consume the test request
        breaker.record_failure()

        assert breaker.state == CircuitState.OPEN

    def test_reset_clears_state(self):
        """Manual reset should clear all state."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)
        breaker.record_failure()
        breaker.record_failure()

        assert breaker.state == CircuitState.OPEN

        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


@pytest.mark.unit
class TestWithCircuitBreakerDecorator:
    """Test with_circuit_breaker decorator."""

    def test_passes_through_when_closed(self):
        """Decorated function should execute when circuit is closed."""
        breaker = CircuitBreaker(name="test")

        @with_circuit_breaker(breaker)
        def my_func():
            return "success"

        result = my_func()
        assert result == "success"

    def test_records_success_on_success(self):
        """Decorator should record success on successful execution."""
        breaker = CircuitBreaker(name="test")
        breaker._failures = 2

        @with_circuit_breaker(breaker)
        def my_func():
            return "success"

        my_func()
        assert breaker.failure_count == 0

    def test_records_failure_on_exception(self):
        """Decorator should record failure on exception."""
        breaker = CircuitBreaker(name="test", failure_threshold=5)

        @with_circuit_breaker(breaker)
        def my_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            my_func()

        assert breaker.failure_count == 1

    def test_raises_circuit_breaker_error_when_open(self):
        """Decorator should raise CircuitBreakerOpenError when open."""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        breaker.record_failure()  # Open the circuit

        @with_circuit_breaker(breaker)
        def my_func():
            return "success"

        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            my_func()

        assert exc_info.value.service_name == "test"

    def test_preserves_function_metadata(self):
        """Decorator should preserve function name and docstring."""
        breaker = CircuitBreaker(name="test")

        @with_circuit_breaker(breaker)
        def my_documented_func():
            """This is my docstring."""
            pass

        assert my_documented_func.__name__ == "my_documented_func"
        assert "docstring" in my_documented_func.__doc__

    def test_does_not_count_circuit_breaker_error_as_failure(self):
        """CircuitBreakerOpenError should not increment failure count."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)
        breaker.record_failure()  # failure_count = 1
        breaker.record_failure()  # Opens circuit, failure_count = 2

        @with_circuit_breaker(breaker)
        def my_func():
            return "success"

        try:
            my_func()
        except CircuitBreakerOpenError:
            pass

        # Should still be 2, not incremented
        assert breaker.failure_count == 2


@pytest.mark.unit
class TestModuleLevelBreakers:
    """Test module-level circuit breaker instances."""

    def test_openai_circuit_exists(self):
        """OpenAI circuit breaker should be defined."""
        assert openai_circuit is not None
        assert openai_circuit.name == "openai_tts"

    def test_gemini_circuit_exists(self):
        """Gemini circuit breaker should be defined."""
        assert gemini_circuit is not None
        assert gemini_circuit.name == "gemini_ai"

    def test_s3_circuit_exists(self):
        """S3 circuit breaker should be defined."""
        assert s3_circuit is not None
        assert s3_circuit.name == "s3_storage"

    def test_breakers_have_appropriate_thresholds(self):
        """Verify threshold configuration."""
        # OpenAI and Gemini - standard threshold
        assert openai_circuit.failure_threshold == 3
        assert gemini_circuit.failure_threshold == 3
        # S3 - higher threshold (more reliable)
        assert s3_circuit.failure_threshold == 5

    def test_breakers_start_closed(self):
        """All breakers should start in closed state."""
        # Note: These might have state from other tests, so reset first
        openai_circuit.reset()
        gemini_circuit.reset()
        s3_circuit.reset()

        assert openai_circuit.state == CircuitState.CLOSED
        assert gemini_circuit.state == CircuitState.CLOSED
        assert s3_circuit.state == CircuitState.CLOSED
