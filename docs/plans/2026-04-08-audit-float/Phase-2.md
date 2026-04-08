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

The implementer must choose between two approaches and execute the chosen one
in a single commit:

- **Option A (preferred):** Remove the `/token` endpoint entirely. Return 410
  Gone with a message pointing at the future ephemeral-token mechanism. The
  Gemini Live frontend caller (`frontend/components/AuthScreen.tsx` or wherever
  it lives) currently breaks; mark the corresponding feature behind a feature
  flag and leave a tracking note in the commit body.
- **Option B:** Keep the endpoint but eliminate the plaintext leak. The
  endpoint must NOT return `settings.GEMINI_API_KEY`. Instead, return a
  short-lived opaque marker plus a 401-on-mismatch instruction for the client
  to upgrade its flow. The marker has no functional value; the goal is to
  eliminate the secret leak while leaving a deprecation path.

The implementer SHOULD pick Option A unless removing the endpoint
breaks a frontend feature already in production. Consult `git log --oneline -- frontend/components/AuthScreen.tsx`
and `frontend/components/AudioRecording.tsx` to determine the call site
status.

**Files to Modify:**

- `backend/src/handlers/lambda_handler.py` -- modify or delete
  `_handle_token_request` (lines 704-756); update routing to surface 410 Gone
  if Option A is taken
- `backend/src/handlers/lambda_handler.py:47-50` -- delete the
  `_token_rate_limit` module-level dict and the `TOKEN_RATE_LIMIT_*`
  constants if and only if the endpoint is removed
- `backend/tests/unit/test_lambda_handler.py` (or wherever the token endpoint
  is tested) -- replace existing token tests with the new contract
- `frontend/components/AuthScreen.tsx` (Option A only) -- remove the
  call to `/token` if a frontend caller exists; otherwise no frontend change
- `docs/API.md` -- intentionally NOT updated here. Phase 6 owns documentation.

**Prerequisites:** None inside this phase.

**Implementation Steps:**

- Locate every caller of `/token`:
  ```bash
  grep -rn "/token" frontend/ backend/
  grep -rn "token_request" backend/
  ```
- If Option A: delete `_handle_token_request`, remove the module-level rate
  limit, remove the routing branch at `lambda_handler.py:597-598`, and add a
  410 Gone fallback in the new router (see Task 2). Update the test file to
  assert 410 Gone.
- If Option B: change the response body to return an opaque value
  (e.g. an HMAC-signed nonce) instead of `settings.GEMINI_API_KEY`. The
  implementer must NOT introduce a new long-lived secret; if Option B requires
  a signing key, derive it from `settings.GEMINI_API_KEY` via HMAC so no new
  config is added. Document the choice in the commit body.
- Either way, eliminate the unbounded `_token_rate_limit` dict.
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`.

**Verification Checklist:**

- [ ] `grep -rn "settings.GEMINI_API_KEY" backend/src/handlers/` returns 0
      hits (the secret is no longer surfaced from a handler)
- [ ] `_token_rate_limit` is deleted OR the rate-limit logic is enforced via a
      mechanism that survives cold start (Option B)
- [ ] New unit test asserts the new endpoint contract (410 Gone OR no plaintext
      key)
- [ ] No existing test that previously asserted on the plaintext key is left
      passing -- all such tests are updated
- [ ] `npm run check` passes

**Testing Instructions:**

- Add a unit test `test_token_endpoint_does_not_leak_api_key` that asserts
  `settings.GEMINI_API_KEY` is not present in the response body, regardless of
  status code.
- Add a unit test `test_token_endpoint_410_gone` (Option A) OR
  `test_token_endpoint_returns_opaque_marker` (Option B).
- If Option A removed a frontend caller, add a unit test in
  `frontend/tests/unit/` that asserts the corresponding component does not
  attempt to fetch `/token`.

**Commit Message Template:**

```text
fix(backend): stop leaking GEMINI_API_KEY from /token endpoint

- /token previously returned settings.GEMINI_API_KEY in the response body
- In-memory rate limiter was per-container and reset on cold start
- (Option A) Remove the endpoint; return 410 Gone with deprecation notice
- (Option B) Return an HMAC-derived opaque marker; rate limit unchanged

The endpoint exists because Google does not yet ship ephemeral Gemini Live
tokens. When that capability arrives, restore an ephemeral-token issuer.
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
  `_handle_download_request`, and `_handle_token_request` (if it survives
  Task 1), add a single shared `_validate_user_id(user_id)` helper that raises
  a 400 error on bad input
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

- [ ] `is_valid_user_id` exists in exactly one place
- [ ] `SummaryRequestModel` and `MeditationRequestModel` reject bad `user_id`
      via Pydantic validation
- [ ] `_handle_job_status_request` and `_handle_download_request` reject bad
      `user_id` with 400
- [ ] Authorization check is extracted to a single helper used by both routes
- [ ] All new tests pass
- [ ] All existing tests continue to pass
- [ ] `npm run check` passes

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
  `_handle_job_status_request`, `_handle_download_request`,
  `_handle_token_request` (if surviving Task 1) by passing each helper through
  a shared CORS-applying wrapper
- `backend/tests/unit/test_lambda_handler.py` -- add routing tests

**Prerequisites:** Task 2 (validator helper exists and is tested).

**Implementation Steps:**

- Define a small `_ROUTES` table at module scope:
  ```python
  _ROUTES = (
      # (method, path-regex, handler)
      ("GET",  re.compile(r"^/?(?:[^/]+/)*job/(?P<job_id>[^/]+)/?$"), _handle_job_status_request),
      ("POST", re.compile(r"^/?(?:[^/]+/)*job/(?P<job_id>[^/]+)/download/?$"), _handle_download_request),
      ("POST", re.compile(r"^/?(?:[^/]+/)*token/?$"), _handle_token_request),  # only if surviving
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

- [ ] `grep -rn "in raw_path" backend/src/handlers/lambda_handler.py` returns
      0 hits
- [ ] `grep -rn "from .middleware import cors_middleware" backend/src/handlers/lambda_handler.py`
      shows ONE import at the top of the file, not three inline imports
- [ ] New routing tests cover:
  - `GET /job/abc` matches the job-status route
  - `GET /production/job/abc` matches the job-status route (stage prefix)
  - `POST /job/abc/download` matches the download route ONLY (not job-status)
  - `POST /token` matches the token route (or returns 410, depending on Task 1)
  - `POST /` falls through to the main handler
- [ ] All existing tests pass
- [ ] `npm run check` passes

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
- Verify `error_handling_middleware` is the *outermost* middleware in the
  decorator stack so it catches anything that escapes the inner middlewares.
  In `lambda_handler.py:536-543`, the order is:
  ```python
  cors_middleware,
  json_middleware,
  method_validation_middleware(["POST"]),
  request_validation_middleware,
  request_size_validation_middleware,
  error_handling_middleware,
  ```
  Note: middleware decorators apply bottom-to-top, so
  `error_handling_middleware` is closest to the inner handler -- it catches
  domain exceptions raised by the handler. CORS is the outermost. This is
  correct; do NOT change the order.
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

- [ ] `json_middleware` no longer has a catch-all `except Exception` around
      the inner handler call
- [ ] `request_validation_middleware` no longer has a catch-all `except
      Exception` around the inner handler call
- [ ] New tests assert domain exceptions surface their `code` and status
- [ ] All existing tests pass
- [ ] `npm run check` passes

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

- [ ] `grep -rn "settings.GEMINI_API_KEY" backend/src/handlers/` returns 0
      hits
- [ ] `grep -rn '"in raw_path"' backend/src/handlers/lambda_handler.py`
      returns 0 hits (use the actual literal `in raw_path` if grep escaping
      complicates this)
- [ ] `grep -c "from .middleware import cors_middleware"
      backend/src/handlers/lambda_handler.py` shows 1 (the top-of-file import)
- [ ] All new tests pass
- [ ] `npm run check` passes
- [ ] No regression in existing test suites

Known limitations after this phase:

- The `LambdaHandler` god object is still 700+ lines -- Phase 4 splits it
- The streaming HLS pipeline still has thread-safety bugs -- Phase 3 fixes
  them
- Job state is still S3-backed with read-modify-write race risk -- Phase 3
  applies in-place mitigations
