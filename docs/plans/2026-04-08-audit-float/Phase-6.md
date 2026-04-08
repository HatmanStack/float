# Phase 6: Doc-Engineer -- Documentation Accuracy and Prevention [DOC-ENGINEER]

## Phase Goal

Bring documentation in sync with the code that lands in Phases 1-5, fix the
drift items called out in `doc-audit.md`, fill the documentation gaps, and
add prevention tooling so future drift is caught at PR time. This phase MUST
NOT change product code -- only documentation files and CI tooling for
documentation.

**Success criteria**

- Every D-tagged drift item from `doc-audit.md` is resolved in `README.md`,
  `CLAUDE.md`, `docs/README.md`, `docs/ARCHITECTURE.md`, or `docs/API.md`
- Every G-tagged gap is documented (HLS flow, token endpoint, retry semantics,
  authorization model, env vars)
- Stale references to `tests/` at the repo root are corrected to
  `frontend/tests/`
- Stale code examples in `docs/API.md` are corrected to match the actual
  async polling contract and the actual download response shape
- A `markdownlint` CI job runs on `.md` files
- A `lychee` link checker CI job runs on `.md` files
- All plan files (including this one) pass `markdownlint`
- `npm run check` is unaffected
- Estimated tokens: ~20000

## Prerequisites

- Phases 1-5 complete and merged
- The implementer who handles this phase MUST read `doc-audit.md` end-to-end
  before starting any task -- the audit is the source of truth for what is
  drift vs what is gap

## Tasks

### Task 1: Fix version drift and stale tests path in top-level docs

**Goal:** Resolve doc-audit drift items D1, D2, D9 and stale items S1, S2,
S3, S4, plus the `EXPO_PUBLIC_ANDROID_CLIENT_ID` (G3) and `G_KEY` (G4) env
var gaps. These are all small, mechanical edits.

**Files to Modify:**

- `README.md` -- update Expo badge from 52+ to 55+, fix the structure block
  to show `frontend/tests/` (not `tests/` at root), remove the "Node.js v24
  LTS" claim (Node 24 is not currently LTS; say "Node.js 24+")
- `CLAUDE.md` -- update the architecture block:
  - "Expo 52 / React Native 0.74" -> "Expo 55 / React Native 0.84 / React 19"
  - Remove the top-level `tests/` line; tests live in `frontend/tests/`
  - Update the test pattern note to point at `frontend/tests/`
- `docs/README.md` -- fix `npm test` description (it is NOT watch mode at the
  root; the root script is `cd frontend && npx jest --forceExit`)
- `docs/README.md` Project Structure block -- fix the `tests/` location
- `docs/ARCHITECTURE.md` Technology Stack table -- update React Native and
  Expo versions to match `package.json`
- `frontend/.env.example` -- already documents `EXPO_PUBLIC_ANDROID_CLIENT_ID`;
  cross-reference it from `docs/README.md`'s env-vars table
- `backend/.env.example` -- the `G_KEY` legacy alias is undocumented in
  `docs/README.md`. Add a single sentence explaining `GEMINI_API_KEY` is
  preferred and `G_KEY` is the legacy alias accepted via `AliasChoices`

**Prerequisites:** None (these are doc-only edits).

**Implementation Steps:**

- Open each file and apply the corrections above. Cross-check against
  `package.json` (Expo `~55.0.7`, React `19.2.3`, RN `0.84.1`).
- The README.md "Quick Start" `npm install --legacy-peer-deps` is correct;
  do not remove the flag.
- The CLAUDE.md "Frontend test patterns" line currently reads
  `*-test.tsx, *-test.ts in tests/frontend/` -- it should read
  `frontend/tests/{unit,integration}/`.
- After edits, run a quick visual audit: `grep -rn "Expo 52" README.md
  CLAUDE.md docs/`. Expected hits: 0.
- `grep -rn "tests/frontend" README.md CLAUDE.md docs/`. Expected hits: 0.
- `grep -rn "Node.js v24 LTS" README.md docs/`. Expected hits: 0.

**Verification Checklist:**

- [x] No occurrence of "Expo 52" in any doc file outside `CHANGELOG.md`
- [x] No occurrence of "tests/frontend" in any doc file
- [x] No occurrence of "Node.js v24 LTS" in any doc file
- [x] `docs/README.md` lists `EXPO_PUBLIC_ANDROID_CLIENT_ID` in the env vars
      table
- [x] `docs/README.md` mentions the `G_KEY` legacy alias
- [x] `markdownlint` (Task 5) passes after these edits

**Commit Message Template:**

```text
docs: refresh version, test layout, and env var references

- README/CLAUDE/docs: Expo 52->55, RN 0.74->0.84, React 18->19
- Fix tests/ path: tests live in frontend/tests/{unit,integration}
- Drop "Node.js v24 LTS"; say "Node.js 24+" (Node 24 is not LTS)
- Document EXPO_PUBLIC_ANDROID_CLIENT_ID and G_KEY legacy alias
```

---

### Task 2: Update `docs/API.md` to match the actual API contract

**Goal:** Resolve doc-audit drift items D3-D8 and stale code examples CE1-CE2.
These are content fixes inside `docs/API.md` reflecting the actual code in
Phases 0-5. Most of the drift exists today; the changes from Phase 2
(`/token` removal or rewrite) and Phase 4 (collapsed validation) are also
captured here.

**Files to Modify:**

- `docs/API.md` -- multiple sections

**Prerequisites:** Phase 2 Task 1 (the `/token` endpoint contract is now
final) and Task 1 above (other docs are consistent).

**Implementation Steps:**

- **D3 -- Download endpoint response shape.** The current docs say
  "Returns the audio file as a downloadable response." The actual code in
  `_handle_download_request` returns JSON `{job_id, download_url, expires_in:
  3600}` (a presigned URL). Rewrite Section 3 ("Download Meditation") to
  document the JSON shape with an example.
- **D4 -- /token endpoint.** Add or remove the section based on Phase 2 Task
  1's choice:
  - If Option A (removed): document the deprecation in a "Removed Endpoints"
    sub-section pointing at the future ephemeral-token mechanism.
  - If Option B (rewritten): document the new opaque marker shape.
- **D5 -- qa_transcript field.** Add `qa_transcript` to the meditation
  request fields table with a description and link to the
  `QATranscriptItem` shape from `backend/src/models/requests.py`.
- **D6 -- intensity type drift.** The summary response example shows
  `intensity` as a string ("high"); the meditation input uses `intensity`
  as a number (0.8). Pick one. The CODE returns string for summary; the
  CODE accepts number-or-string for meditation float input. Document both,
  clearly labeled.
- **D7 -- error text for invalid inference_type.** The current doc reads
  "inference_type must be 'summary' or 'meditation'"; the code raises
  `f"Invalid inference_type: {inference_type}"`. Update the error example.
- **D8 -- job-status response.** The example response omits `streaming`,
  `download`, and `generation_attempt` fields. Add a complete example
  showing all fields actually returned by `handle_job_status`.
- **CE1 -- polling loop missing playlist_url.** Update the JS example to
  show how to read `job.streaming?.playlist_url` once it becomes available.
- **CE2 -- meditation example treats response as sync.** The "Example 3"
  JS snippet treats `result.body.base64` as immediately available. Replace
  with a polling example that calls `/job/{id}` and reads
  `job.result.base64` after `status === "completed"`.
- **G6 -- authorization documented.** Add a paragraph to the "Authentication"
  section explaining the privacy-first model: `user_id` is client-generated,
  guest mode is supported, and `_authorize_job_access` enforces ownership
  via 403 on mismatch.

**Verification Checklist:**

- [x] Section 3 "Download Meditation" documents the JSON response shape
- [x] Section 2 meditation request fields table includes `qa_transcript`
- [x] Job-status response example includes `streaming`, `download`,
      `generation_attempt`
- [x] The "Example 3" JS snippet polls instead of treating the meditation
      response as sync
- [x] The "Client Usage" example reads `job.streaming?.playlist_url`
- [x] `markdownlint` passes
- [x] `lychee` (Task 5) reports no broken links

**Commit Message Template:**

```text
docs(api): bring API.md in sync with the actual handler contract

- Section 3 download: JSON {job_id, download_url, expires_in}
- Section 2 meditation: add qa_transcript field; complete job-status example
- Update polling example to use streaming.playlist_url
- Convert Example 3 JS snippet to async/poll pattern
- Document authorization model and /token deprecation
```

---

### Task 3: Document HLS streaming, retry semantics, and Gemini Live token flow

**Goal:** Doc-audit gaps G1, G2, G5: the HLS flow, token endpoint behavior,
and `MAX_GENERATION_ATTEMPTS` retry semantics are not documented anywhere.
Add a new section to `docs/ARCHITECTURE.md` covering them, with a sequence
diagram for the async self-invoking Lambda meditation flow.

**Files to Modify:**

- `docs/ARCHITECTURE.md` -- add a "Meditation Generation Flow" section

**Prerequisites:** Tasks 1 and 2 above.

**Implementation Steps:**

- Add a new top-level section to `docs/ARCHITECTURE.md` with three subsections:
  - **Async self-invocation**: A simple ASCII or mermaid sequence diagram
    showing Client -> POST / -> Lambda creates job -> Lambda invokes itself
    via `lambda_client.invoke(InvocationType="Event")` -> returns job_id ->
    Client polls GET /job/{id}.
  - **HLS streaming pipeline**: Describe the streaming variant (`process_stream_to_hls`),
    the `_StreamState` lock, the watcher thread, the fade-segment append, and
    the `tts_cache` retry path. Include the constants: `HLS_SEGMENT_DURATION`,
    `HLS_FADE_DURATION_SECONDS`, `MAX_GENERATION_ATTEMPTS`,
    `TTS_WORDS_PER_MINUTE`.
  - **Token endpoint** (whether removed or rewritten in Phase 2): explain the
    Gemini Live use case and the deprecation status.
- The retry semantics paragraph names `MAX_GENERATION_ATTEMPTS = 3` and
  links to the Phase 3 Task 4 retry-loop change.
- Use ` ```text ` or ` ```mermaid ` for diagrams. Markdownlint requires a
  language tag on every fenced block.

**Verification Checklist:**

- [x] `docs/ARCHITECTURE.md` has a "Meditation Generation Flow" section
- [x] Diagrams use a language tag in every fenced code block
- [x] `MAX_GENERATION_ATTEMPTS`, `HLS_SEGMENT_DURATION`,
      `TTS_WORDS_PER_MINUTE` are mentioned with their current values
- [x] The token endpoint section documents Phase 2 Task 1's choice
- [x] `markdownlint` passes

**Commit Message Template:**

```text
docs(architecture): document async meditation flow and HLS pipeline

- Add sequence diagram for self-invoking Lambda meditation flow
- Document HLS streaming pipeline, watcher thread, fade-append
- Explain MAX_GENERATION_ATTEMPTS retry semantics
- Document /token endpoint deprecation per Phase 2 Task 1
```

---

### Task 4: Resolve doc structure issues (deduplication and indexing)

**Goal:** Doc-audit structural items ST1-ST3, plus CF2 (deploy parameter
table drift). The repo has two README files duplicating environment and
deploy content with drifted tables. Establish the canonical hierarchy from
Phase 0 ADR-5 and remove duplication.

**Files to Modify:**

- `README.md` (repo root) -- shrink the "Deployment" parameter table to a
  one-line link pointing at `docs/README.md` for the canonical version
- `docs/README.md` -- become the single source of truth for the deploy
  parameter table; merge any unique entries from the root README
- `CLAUDE.md` -- replace its architecture duplication with a single link to
  `docs/ARCHITECTURE.md`. Keep CLAUDE.md focused on commands and
  conventions only (per Phase 0 ADR-5)
- `docs/README.md` -- add an index entry for `docs/plans/` so the plans tree
  is discoverable

**Prerequisites:** Tasks 1, 2, 3 (the canonical sources are already correct).

**Implementation Steps:**

- Read both deploy parameter tables and merge into the `docs/README.md` one.
  Confirm against `backend/template.yaml` that every parameter listed
  actually exists.
- Replace the root `README.md` deploy section with:
  ```markdown
  ## Deployment

  ```bash
  npm run deploy
  ```

  See [docs/README.md#deployment](docs/README.md#deployment) for the
  canonical deploy parameter list.
  ```
- In `CLAUDE.md`, the "Architecture" block is currently a 30-line duplicate
  of `docs/ARCHITECTURE.md`. Replace it with a one-paragraph summary plus
  a link:
  ```markdown
  ## Architecture

  See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the canonical
  description.

  Quick reference:

  - frontend/  Expo / React Native / TypeScript
  - backend/   Python 3.13 / AWS Lambda
  - frontend/tests/  Jest test suites
  - docs/      API.md, ARCHITECTURE.md, plans/
  ```
- In `docs/README.md`, add a new bullet under "Documentation":
  - `[plans/](plans/) - Remediation plans and audit history`

**Verification Checklist:**

- [x] Only one canonical deploy parameter table exists (in `docs/README.md`)
- [x] `CLAUDE.md` no longer duplicates `docs/ARCHITECTURE.md`'s content
- [x] `docs/README.md` indexes `docs/plans/`
- [x] `markdownlint` passes
- [x] `lychee` reports no broken links

**Commit Message Template:**

```text
docs: deduplicate and reindex documentation tree

- README.md: link to docs/README.md for deploy params; remove duplicate
- CLAUDE.md: link to docs/ARCHITECTURE.md; keep commands/conventions only
- docs/README.md: index docs/plans/ tree
```

---

### Task 5: Add markdownlint CI job

**Goal:** Doc-audit prevention tooling. Add a markdownlint CI step that
catches drift on PR. The plan files in this remediation must pass the rules
already (this phase enforces them).

**Files to Modify:**

- `.github/workflows/ci.yml` -- add a `markdownlint` job
- `.markdownlint.json` (new) -- minimal config that matches the rules used
  in the plan files (allow long lines in code blocks, require language tags
  on fenced blocks, etc.)

**Prerequisites:** Tasks 1-4 (all docs are correct).

**Implementation Steps:**

- Create `.markdownlint.json` at the repo root:
  ```json
  {
    "default": true,
    "MD013": false,
    "MD024": { "siblings_only": true },
    "MD033": false,
    "MD041": false
  }
  ```
  - MD013 (line length): off, since prose lines vary and code blocks are
    common
  - MD024 (no duplicate headings): siblings only, so per-task
    "Verification Checklist" headings don't conflict
  - MD033 (inline HTML): off, the README banners use HTML
  - MD041 (first line is a heading): off, banners come first
- Add a job to `.github/workflows/ci.yml`:
  ```yaml
    markdownlint:
      name: Markdown Lint
      runs-on: ubuntu-latest
      timeout-minutes: 5
      steps:
        - uses: actions/checkout@v6
        - uses: DavidAnson/markdownlint-cli2-action@v23
          with:
            globs: |
              **/*.md
              !node_modules/**
              !backend/.aws-sam/**
              !**/CHANGELOG.md
  ```

  Version note: `DavidAnson/markdownlint-cli2-action@v23` is the latest
  major tag as of 2026-04-08 (v23.0.0 released 2026-03-26). Pin to `v23`
  (the floating major tag) so point releases pick up automatically.
  Earlier drafts of this task pinned `v17`, which is a stale major; do not
  revert. If a reviewer prefers SHA pinning, the v23.0.0 tag is at
  `DavidAnson/markdownlint-cli2-action@<sha>` -- look up the SHA at tag
  push time and pin that instead.
- Run markdownlint locally over the docs and plan files; fix any issues by
  editing the docs (NOT by adding ignores). The goal is that every plan
  file already passes.
- Add `markdownlint` to the `status-check` job's `needs:` list.

**Verification Checklist:**

- [x] `.markdownlint.json` exists at repo root with the rules above
- [x] `markdownlint` job is in CI and required
- [x] Every `.md` file under `docs/`, repo root, and `docs/plans/` passes the
      rules (CHANGELOG.md is excluded; it has its own format)
- [x] `npm run check` unchanged

**Commit Message Template:**

```text
ci: add markdownlint job for documentation linting

- .markdownlint.json: language tags on fenced blocks, sibling headings only
- markdownlint-cli2-action runs on every PR
- Excludes node_modules, .aws-sam build, and CHANGELOG
```

---

### Task 6: Add lychee link checker

**Goal:** Doc-audit broken-link detection. Add a CI job that runs
`lychee-action` on all `.md` files. Today no broken links exist; this is
purely preventive.

**Files to Modify:**

- `.github/workflows/ci.yml` -- add a `link-check` job
- `lychee.toml` (new, optional) -- configure exclusions if needed

**Prerequisites:** Task 5 (markdownlint already in place).

**Implementation Steps:**

- Add a job to `.github/workflows/ci.yml`:
  ```yaml
    link-check:
      name: Link Check
      runs-on: ubuntu-latest
      timeout-minutes: 5
      steps:
        - uses: actions/checkout@v6
        - uses: lycheeverse/lychee-action@v2
          with:
            args: >-
              --no-progress
              --exclude-mail
              --exclude '^https://your-lambda-url'
              --exclude '^https://www.apache.org/licenses/LICENSE-2.0.html'
              './**/*.md'
              '!./node_modules/**'
              '!./backend/.aws-sam/**'
            fail: true
  ```

  Version note: `lycheeverse/lychee-action@v2` is the current major tag
  (pointing at v2.8.0 as of 2026-02-17). Verified to exist at tag-pin time.
  Pin the floating `v2` so point releases pick up automatically.
- The `your-lambda-url` exclusion handles the placeholder in `docs/API.md`
  and `frontend/.env.example`.
- Add `link-check` to the `status-check` job's `needs:` list.
- Run lychee locally if available
  (`docker run --rm -it -v $PWD:/input lycheeverse/lychee /input`).

**Verification Checklist:**

- [x] `.github/workflows/ci.yml` defines a `link-check` job
- [x] `link-check` is in `status-check` `needs`
- [x] Lychee passes locally over all `.md` files
- [x] `npm run check` unchanged

**Commit Message Template:**

```text
ci: add lychee link checker for documentation

- Runs on every PR
- Excludes placeholder Lambda URL and license link
- Required by status-check
```

---

## Phase Verification

After all six tasks land:

- [x] Every D, G, S, CE, CF, ST item in `doc-audit.md` is resolved or moved
      to "Resolved" with a justification
- [x] `markdownlint` and `lychee` jobs are in CI and required
- [x] No `.md` file references "Expo 52", "React Native 0.74", or
      "tests/frontend"
- [x] `docs/API.md` Section 3 documents the JSON download response
- [x] `docs/ARCHITECTURE.md` has a "Meditation Generation Flow" section
- [x] `CLAUDE.md` no longer duplicates `docs/ARCHITECTURE.md`
- [x] `docs/README.md` is the canonical deploy parameter source
- [x] `npm run check` passes (no product-code touched)

Known limitations after this phase:

- `CHANGELOG.md` is excluded from markdownlint -- it has its own format
- The plan files for older audits in `docs/plans/2026-03-15-audit-float/`
  may not pass the new rules; the `.markdownlint.json` exclusions cover them
  if needed, OR a follow-up plan can polish them
- No automated drift detection between code and docs -- that requires
  custom tooling outside the audit scope
