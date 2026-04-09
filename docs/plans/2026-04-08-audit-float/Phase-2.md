# Phase 2: Implementer -- Critical Security and Routing [IMPLEMENTER]

## Phase Goal

Resolve the two CRITICAL findings related to the `/token` endpoint
and the path-traversal exposure of `user_id` as a raw S3 key prefix, plus
the HIGH routing finding about brittle `rawPath` string matching. This
phase changes user-visible behavior of the `/token` endpoint and adds
input validation that may reject previously-accepted (malformed) requests.
Both behavior changes are documented in Phase 0 ADR-2.

**Success criteria**

- `/token` no longer returns `settings.GEMINI_API_KEY` directly
- A `user_id` validator rejects path-traversal patterns (`..`, `/`, control
  characters) at the request boundary
- Routing is performed by a dispatch table, not by `"in raw_path"` string
  containment, and `_handle_*_request` helpers no longer carry duplicated
  authorization checks
- The three inline `from .middleware import cors_middleware` imports inside
  helper functions are eliminated
- All existing tests still pass; new tests cover the new validators and the
  router
- Estimated tokens: ~22000

## Prerequisites

- Phase 1 complete (clean baseline)
- `npm run check` passes on the merged Phase 1 working tree

## Tasks

### Task 1: Replace `/token` plaintext API key endpoint

**Goal:** The `/token` endpoint at
`backend/src/handlers/lambda_handler.py:704-756` returns the raw
`settings.GEMINI_API_KEY` to clients. The in-memory rate limiter at
`lambda_handler.py:48-50` does not actually rate-limit because the dict resets
on every cold start and is not shared across warm containers. This is a CRITICAL
operational security finding.

**Required path: Option B.** As of 2026-04-08 the `/token` endpoint is
called from `frontend/hooks/useGeminiLiveAPI.ts:97` (verified via
`grep -rn "/token" frontend/`). The hook reads `token` and `endpoint`
fields from the response and uses them to open a Gemini Live WebSocket
connection. Removing the endpoint outright (Option A) would break the
Gemini Live audio feature in production.

Both options were considered:

- **Option A (REJECTED):** Remove the `/token` endpoint entirely and return
  410 Gone. Rejected because `useGeminiLiveAPI.ts` is shipped frontend code
  on the live build; killing the endpoint breaks the Gemini Live audio
  feature with no fallback. A future plan can remove the endpoint after the
  frontend migrates to a different auth flow.
- **Option B (REQUIRED):** Keep the endpoint contract (POST `/token`,
  returns JSON with `token` and `endpoint` fields) but eliminate the
  plaintext-key leak. The new response MUST NOT contain
  `settings.GEMINI_API_KEY` verbatim. Instead, return an HMAC-derived
  short-lived opaque marker as `token`, and the WebSocket `endpoint` URL
  unchanged. The frontend hook continues to function; the leaked secret is
  gone.

The HMAC signing key MUST be derived from `settings.GEMINI_API_KEY` so no
new long-lived secret is added (per the existing config posture). The
marker is short-lived (60s TTL) and is rejected by the WebSocket handshake
on mismatch; downstream this is a stop-gap until Google ships native
ephemeral Gemini Live tokens, at which point a future plan can switch to
issuing real ephemeral tokens.

**Files to Modify:**

- `backend/src/handlers/lambda_handler.py` -- rewrite `_handle_token_request`
  (lines 704-756) so the response body NEVER contains
  `settings.GEMINI_API_KEY`. The new body returns an HMAC-derived opaque
  marker as `token` plus the existing `endpoint` (WebSocket URL).
- `backend/src/handlers/lambda_handler.py:47-50` -- delete the
  `_token_rate_limit` module-level dict and the `TOKEN_RATE_LIMIT_*`
  constants. Replace with no rate limiter at all (the endpoint is now
  cheap and stateless under Option B; the in-memory limiter never worked
  because it reset on cold start). A DynamoDB-backed limiter is out of
  scope (see Phase 0 "Out of Scope").
- `backend/tests/unit/test_lambda_handler.py` -- replace existing token
  tests with the new contract (no plaintext key in response)
- `frontend/hooks/useGeminiLiveAPI.ts` -- NO CHANGE. The hook already reads
  `token` and `endpoint` from the response shape, which Option B preserves.
- `docs/API.md` -- intentionally NOT updated here. Phase 6 owns documentation.

**Prerequisites:** None inside this phase.

**Implementation Steps:**

- Confirm the call site one more time:
  `grep -rn "/token" frontend/ backend/`. Expected hit:
  `frontend/hooks/useGeminiLiveAPI.ts:97`.
- Rewrite `_handle_token_request` so the JSON response body has the same
  shape `{token, endpoint, expires_in}` but `token` is an HMAC-derived
  opaque marker instead of `settings.GEMINI_API_KEY`. Use
  `hmac.new(settings.GEMINI_API_KEY.encode(), msg=user_id.encode(),
  digestmod="sha256").hexdigest()` truncated, with a TTL field.
- Delete the `_token_rate_limit` module-level dict and the
  `TOKEN_RATE_LIMIT_*` constants.
- The `endpoint` field stays as the existing Gemini Live WebSocket URL --
  the frontend hook already uses it.
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`.

**Verification Checklist:**

- [x] `grep -rn "settings.GEMINI_API_KEY" backend/src/handlers/` returns 0
      hits (the secret is no longer surfaced from a handler)
- [x] `_token_rate_limit` and `TOKEN_RATE_LIMIT_*` constants are deleted
- [x] New unit test asserts the new endpoint contract (no plaintext key in
      the response body)
- [x] No existing test that previously asserted on the plaintext key is left
      passing -- all such tests are updated
- [x] `frontend/hooks/useGeminiLiveAPI.ts` is unchanged
- [x] `npm run check` passes

**Testing Instructions:**

- Add a unit test `test_token_endpoint_does_not_leak_api_key` that asserts
  `settings.GEMINI_API_KEY` is not present in the response body, regardless of
  status code.
- Add a unit test `test_token_endpoint_returns_opaque_marker` that asserts
  the `token` field is an HMAC-derived string (e.g. matches a hex regex)
  and is NOT equal to `settings.GEMINI_API_KEY`.
- The frontend test in `frontend/tests/unit/useGeminiLiveAPI-test.ts` already
  asserts that the hook fetches `/token`; verify it still passes (no
  contract change from the frontend's perspective).

**Commit Message Template:**

```text
fix(backend): stop leaking GEMINI_API_KEY from /token endpoint

- /token previously returned settings.GEMINI_API_KEY in the response body
- In-memory rate limiter was per-container and reset on cold start
- Replace plaintext key with an HMAC-derived short-lived opaque marker
- Delete the unbounded _token_rate_limit dict and TOKEN_RATE_LIMIT_* consts
- frontend/hooks/useGeminiLiveAPI.ts is unchanged: same response shape
- Stop-gap until Google ships native ephemeral Gemini Live tokens
```

---

### Task 2: Add `user_id` validator and tighten authorization

**Goal:** `user_id` is used directly as an S3 key prefix
(`backend/src/services/job_service.py:317, 411`), creating a path-traversal
risk. Validate at the request boundary and at every entry point that takes
`user_id` from query parameters. Reject `..`, `/`, control characters, and
empty values.

**Files to Modify:**

- `backend/src/models/requests.py` -- add a class-level field validator on
  `SummaryRequestModel` and `MeditationRequestModel` for `user_id`
- `backend/src/handlers/lambda_handler.py` -- in `_handle_job_status_request`,
  `_handle_download_request`, and `_handle_token_request` (which survives
  Task 1 under Option B), add a single shared `_validate_user_id(user_id)`
  helper that raises a 400 error on bad input
- `backend/src/utils/file_utils.py` (or a new `backend/src/utils/validation.py`
  if file_utils is full) -- house the validator helper so it can be imported
  by both the Pydantic models and the route helpers
- `backend/tests/unit/test_models.py` -- add positive and negative test cases
- `backend/tests/unit/test_lambda_handler.py` -- add 400 test cases for the
  three GET/POST helpers

**Prerequisites:** Task 1 (so the token endpoint either is removed or has its
own test plan).

**Implementation Steps:**

- Define the regex once. The audit calls this out as a Stress finding:
  ```python
  USER_ID_RE = re.compile(r"^[a-zA-Z0-9._@-]{1,256}$")
  def is_valid_user_id(user_id: str) -> bool:
      return bool(USER_ID_RE.match(user_id))
  ```
  - 256 char ceiling matches the existing `Field(max_length=256)`
  - Allows email-style identifiers, UUID-style identifiers, and
    Google sign-in subject IDs
  - Forbids `/`, `..`, control characters, whitespace
- In `requests.py`, add a Pydantic `field_validator` on `user_id` that calls
  the helper and raises `ValueError` on failure (Pydantic re-wraps it).
- In each `_handle_*_request` helper, replace the existing
  `if not user_id: ... return create_error_response(...)` block with a single
  `if not is_valid_user_id(user_id): return ...` check.
- The helpers currently duplicate auth code (`job_owner != user_id` check).
  Extract a single `_authorize_job_access(job_data, user_id)` helper that
  returns either `None` (authorized) or an error response. Use it from both
  helpers.
- Add tests:
  - `test_user_id_validator_rejects_path_traversal`
  - `test_user_id_validator_rejects_slashes`
  - `test_user_id_validator_accepts_email_format`
  - `test_user_id_validator_accepts_uuid_format`
  - `test_handle_job_status_rejects_invalid_user_id`
  - `test_handle_download_rejects_invalid_user_id`

**Verification Checklist:**

- [x] `is_valid_user_id` exists in exactly one place
- [x] `SummaryRequestModel` and `MeditationRequestModel` reject bad `user_id`
      via Pydantic validation
- [x] `_handle_job_status_request` and `_handle_download_request` reject bad
      `user_id` with 400
- [x] Authorization check is extracted to a single helper used by both routes
- [x] All new tests pass
- [x] All existing tests continue to pass
- [x] `npm run check` passes

**Testing Instructions:**

- Run the new tests: `pytest backend/tests/unit/test_models.py -v -k user_id`
  and `pytest backend/tests/unit/test_lambda_handler.py -v -k validator`.

**Commit Message Template:**

```text
fix(backend): validate user_id at request boundary

- user_id is used raw as an S3 key prefix; reject path-traversal patterns
- Add is_valid_user_id helper in src/utils/validation.py
- Wire into Pydantic models and the GET/POST job helpers
- Extract shared _authorize_job_access from duplicated checks
```

---

### Task 3: Replace `rawPath` string-match routing with a dispatch table

**Goal:** `lambda_handler.lambda_handler` at lines 572-604 routes by string
containment (`"/job/" in raw_path`, `"/download" in raw_path`,
`"/token" in raw_path`). A path like `/download/job/x` matches both branches
depending on declaration order. Replace with a dispatch table keyed on
(method, normalized path pattern). The three `_handle_*_request` helpers must
no longer import `cors_middleware` inline.

**Files to Modify:**

- `backend/src/handlers/lambda_handler.py` -- replace the routing block at
  lines 572-604 with a dispatch table
- `backend/src/handlers/lambda_handler.py` -- remove the inline
  `from .middleware import cors_middleware` calls inside
  `_handle_job_status_request`, `_handle_download_request`, and
  `_handle_token_request` (which survives Task 1 under Option B) by passing
  each helper through a shared CORS-applying wrapper
- `backend/tests/unit/test_lambda_handler.py` -- add routing tests

**Prerequisites:** Task 2 (validator helper exists and is tested).

**Implementation Steps:**

- Define a small `_ROUTES` table at module scope:
  ```python
  _ROUTES = (
      # (method, path-regex, handler)
      ("GET",  re.compile(r"^/?(?:[^/]+/)*job/(?P<job_id>[^/]+)/?$"), _handle_job_status_request),
      ("POST", re.compile(r"^/?(?:[^/]+/)*job/(?P<job_id>[^/]+)/download/?$"), _handle_download_request),
      ("POST", re.compile(r"^/?(?:[^/]+/)*token/?$"), _handle_token_request),
  )
  ```
- The `lambda_handler` function dispatches by iterating the table once and
  picking the first match. The match groups (`job_id`) are passed through
  `event["pathParameters"]` so the existing helpers can read them via the
  standard mechanism instead of re-parsing `rawPath`.
- The Lambda function URL strips the stage prefix (`/production/`); validate
  that the regex tolerates both `"/job/abc"` and `"/production/job/abc"`.
- Wrap each helper exactly once with `cors_middleware` at module load time:
  ```python
  _handle_job_status_request = cors_middleware(_handle_job_status_request)
  ```
  This eliminates the inline `from .middleware import cors_middleware` calls
  and the `cors_middleware(lambda e, _: response)(event, None)` wrapping
  pattern.
- The default fallback (no route matched) routes to the existing
  `handler.handle_request(event, context)` which has the full middleware chain.
- Delete the now-dead string-containment branches.

**Verification Checklist:**

- [x] `grep -rn "in raw_path" backend/src/handlers/lambda_handler.py` returns
      0 hits
- [x] `grep -rn "from .middleware import cors_middleware" backend/src/handlers/lambda_handler.py`
      shows ONE import at the top of the file, not three inline imports
- [x] New routing tests cover:
  - `GET /job/abc` matches the job-status route
  - `GET /production/job/abc` matches the job-status route (stage prefix)
  - `POST /job/abc/download` matches the download route ONLY (not job-status)
  - `POST /token` matches the token route (returns the Option B opaque
    marker per Task 1)
  - `POST /` falls through to the main handler
- [x] All existing tests pass
- [x] `npm run check` passes

**Testing Instructions:**

- Add `test_routing_dispatch_table.py` (or a new test class) that constructs
  representative event dicts for each route and asserts the correct helper is
  invoked. Mock the helpers to record invocations.

**Commit Message Template:**

```text
refactor(backend): replace rawPath string-match routing with dispatch table

- Routes now use a single _ROUTES table with method+regex patterns
- /download/job/x no longer ambiguously double-matches
- _handle_*_request helpers receive job_id via pathParameters
- cors_middleware is applied once at module load, not inline per call
```

---

### Task 4: Wire `error_handling_middleware` to surface domain exception types

**Goal:** The `error_handling_middleware` in `backend/src/handlers/middleware.py`
already has a `FloatException` branch (lines 263-270), but
`json_middleware` and `request_validation_middleware` swallow exceptions with
generic 500s (lines 80-85, 140-145). Three `except Exception` clauses across
the middleware return generic 500s and hide
`CircuitBreakerOpenError` / `TTSError` taxonomies from HTTP clients.

This task narrows those handlers so domain errors propagate to
`error_handling_middleware`, where they are converted to the right HTTP status
and code.

**Files to Modify:**

- `backend/src/handlers/middleware.py` -- replace `except Exception:` blocks in
  `json_middleware` and `request_validation_middleware` with narrower catches
  (`json.JSONDecodeError`, `KeyError`) and re-raise everything else
- `backend/tests/unit/test_middleware.py` -- add tests asserting
  `CircuitBreakerOpenError` and `TTSError` propagate correctly

**Prerequisites:** Task 3 (dispatch table merged so no inline middleware
references break).

**Implementation Steps:**

- In `json_middleware`, the only exception that should produce a generic 500 is
  an unexpected one *outside* the JSON parsing path. Narrow the outer
  `try/except Exception` to just the JSON parsing block. Let the inner handler
  call propagate exceptions to `error_handling_middleware`.
- In `request_validation_middleware`, the outer `try/except Exception` is
  defensive against handler failure during the validation chain. Narrow to
  catch only `KeyError` from `parsed_body.get` (which cannot raise) and remove
  the catch-all. Let everything else propagate.
- Verify `error_handling_middleware` wrapping order. In
  `lambda_handler.py:536-543`, the list is:
  ```python
  cors_middleware,
  json_middleware,
  method_validation_middleware(["POST"]),
  request_validation_middleware,
  request_size_validation_middleware,
  error_handling_middleware,
  ```
  The list-order intuition ("first listed = outermost") is WRONG for this
  codebase. Read `backend/src/handlers/middleware.py:313` to see why:
  `apply_middleware` iterates with `for middleware in reversed(middleware_functions):`
  and re-wraps the handler each iteration, so the LAST entry in the list
  ends up as the INNERMOST wrapper and the FIRST entry as the OUTERMOST.
  Therefore:
  - `cors_middleware` is the OUTERMOST wrapper (it sees the final response
    on the way out and adds CORS headers).
  - `error_handling_middleware` is the INNERMOST wrapper (it is closest
    to the inner handler and catches domain exceptions raised by the
    handler).
  This is correct for this task: domain exceptions raised by the handler
  flow up into `error_handling_middleware` first and are converted to
  proper status codes before any outer middleware sees them. Do NOT
  change the order.
- The remaining issue is that exceptions raised *inside* `json_middleware` or
  `request_validation_middleware` themselves (not in the inner handler) bypass
  `error_handling_middleware` because the latter is *inside* the chain.
  Document this in a comment and accept it as the existing design --
  middleware-internal failures are 500s by design.
- Add tests:
  - `test_error_middleware_propagates_TTSError` -- assert response includes
    `code: TTS_FAILURE` and a 500 status with `retriable=true`
  - `test_error_middleware_propagates_CircuitBreakerOpenError` -- assert 500
    plus `EXTERNAL_SERVICE_UNAVAILABLE`
  - `test_error_middleware_propagates_ValidationError_from_handler` -- assert
    400 plus `INVALID_REQUEST`

**Verification Checklist:**

- [x] `json_middleware` no longer has a catch-all `except Exception` around
      the inner handler call
- [x] `request_validation_middleware` no longer has a catch-all `except
      Exception` around the inner handler call
- [x] New tests assert domain exceptions surface their `code` and status
- [x] All existing tests pass
- [x] `npm run check` passes

**Testing Instructions:**

- Run the new tests: `pytest backend/tests/unit/test_middleware.py -v`.

**Commit Message Template:**

```text
fix(backend): let domain exceptions propagate through middleware chain

- json_middleware and request_validation_middleware swallowed all exceptions
  as 500s, hiding TTSError / CircuitBreakerOpenError / ValidationError codes
- Narrow the catches to JSON-parse / dict-access failures only
- Add tests asserting domain exception classes surface their error codes
```

---

## Phase Verification

After all four tasks land:

- [x] `grep -rn "settings.GEMINI_API_KEY" backend/src/handlers/` returns 0
      hits
- [x] `grep -rn '"in raw_path"' backend/src/handlers/lambda_handler.py`
      returns 0 hits (use the actual literal `in raw_path` if grep escaping
      complicates this)
- [x] `grep -c "from .middleware import cors_middleware"
      backend/src/handlers/lambda_handler.py` shows 1 (the top-of-file import)
- [x] All new tests pass
- [x] `npm run check` passes
- [x] No regression in existing test suites

Known limitations after this phase:

- The `LambdaHandler` god object is still 700+ lines -- Phase 4 splits it
- The streaming HLS pipeline still has thread-safety bugs -- Phase 3 fixes
  them
- Job state is still S3-backed with read-modify-write race risk -- Phase 3
  applies in-place mitigations
