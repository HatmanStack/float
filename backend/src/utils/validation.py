"""Input validation helpers for the Float backend.

This module hosts the canonical ``user_id`` validator. The identifier is used
directly as an S3 key prefix by ``JobService`` (see ``job_service.py:317,
411``) which makes it a privileged input: unvalidated values allow
path-traversal into other users' namespaces. The validator is imported from
both the Pydantic request models and the route helpers in
``lambda_handler.py`` so a single regex owns the contract.

The broader identity overhaul (server-minted UUIDs or JWTs) is explicitly
out of scope for the audit remediation plan. See Phase 0 "Out of Scope" for
the justification.
"""

import re

# Accepts email-style identifiers, UUID-style identifiers, and Google sign-in
# subject IDs. Explicitly forbids ``/``, ``..`` (no dot-segments), control
# characters, and any whitespace. The 256 character ceiling mirrors the
# existing ``Field(max_length=256)`` on the Pydantic models.
_USER_ID_RE = re.compile(r"^[a-zA-Z0-9._@-]{1,256}$")


def is_valid_user_id(user_id: str) -> bool:
    """Return True if ``user_id`` is a safe S3 key prefix.

    This function is intentionally strict: any character outside the
    allow-list ``[a-zA-Z0-9._@-]`` is rejected, as are empty strings and
    values longer than 256 characters. Dot-segments (``..``) are also
    rejected explicitly because the per-character allow-list admits them
    trivially but they are the canonical path-traversal primitive.
    """
    if not isinstance(user_id, str):
        return False
    if _USER_ID_RE.match(user_id) is None:
        return False
    # Explicitly reject path-traversal dot-segments. The per-character
    # allow-list admits ``..`` because ``.`` is on the list; this check is
    # defence-in-depth on top of the S3 key prefix use.
    if ".." in user_id:
        return False
    return True
