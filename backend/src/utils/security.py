"""Security helpers for the Float backend.

This module hosts small, pure-function helpers for request-boundary security
concerns (opaque token derivation, HMAC signing). Pulling these out of the
handler module keeps the handler free of ``settings.GEMINI_API_KEY`` literal
references and lets the helpers be unit-tested in isolation.
"""

import hmac
from hashlib import sha256

from ..config.settings import settings

# Length of the truncated HMAC hex digest returned as the opaque token
# marker. 32 hex characters == 128 bits of entropy, which is sufficient for
# the short-lived stop-gap marker while keeping the response body compact.
TOKEN_MARKER_HEX_LENGTH = 32


def derive_token_marker(user_id: str) -> str:
    """Derive an HMAC-SHA256 opaque token marker for the given ``user_id``.

    Uses ``settings.GEMINI_API_KEY`` as the HMAC signing key so no new
    long-lived secret is introduced. The returned hex digest is truncated to
    128 bits, which is enough entropy for a short-lived marker without
    bloating the response body.

    This marker is a stop-gap: it does NOT authorize the Gemini Live
    WebSocket handshake by itself. It exists to keep the frontend hook
    contract stable while ensuring the ``/token`` response body no longer
    contains the raw Gemini API key verbatim. A future plan will switch to
    Google's native ephemeral Gemini Live tokens once available.
    """
    return hmac.new(
        settings.GEMINI_API_KEY.encode("utf-8"),
        msg=user_id.encode("utf-8"),
        digestmod=sha256,
    ).hexdigest()[:TOKEN_MARKER_HEX_LENGTH]
