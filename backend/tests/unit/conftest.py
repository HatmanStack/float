"""Shared fixtures for backend unit tests.

``LambdaHandler.__init__`` eagerly constructs ``genai.Client`` (Gemini) and
``OpenAITTSProvider`` -> ``openai.OpenAI``, both of which raise at construction
time when no API key is present. CI has no keys, so any unit test that builds a
handler/provider (e.g. ``test_lambda_handler.py``, ``test_services.py``) fails
at construction. Mock both client constructors for all unit tests so
initialization doesn't require real credentials.

(Integration and e2e tests handle credentials via their own conftests — skipping
or injecting — so this only covers ``tests/unit``.)
"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _mock_external_ai_clients():
    """Prevent genai.Client / openai.OpenAI from requiring real keys in CI."""
    with patch("src.services.gemini_service.genai.Client"), patch(
        "src.providers.openai_tts.openai.OpenAI"
    ):
        yield
