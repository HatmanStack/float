---
type: doc-health
date: 2026-04-08
language_stack: js-ts-python
prevention_tooling: markdownlint-lychee
---

## DOCUMENTATION AUDIT

### SUMMARY
- Docs scanned: 7 (README.md, CLAUDE.md, CONTRIBUTING.md, CHANGELOG.md, docs/README.md, docs/API.md, docs/ARCHITECTURE.md) plus frontend test READMEs
- Code modules scanned: backend handlers/models/config/services/exceptions; frontend components/hooks/env
- Total findings: 9 drift, 6 gaps, 4 stale, 0 broken links, 2 stale code examples, 2 config drift, 3 structure issues

### DRIFT

1. **Expo/React/RN versions stale across docs.** `README.md` badge + `docs/README.md` badge show "Expo 52+"; `docs/ARCHITECTURE.md:93-94` states "React Native 0.74, Expo 52". `package.json` pins `expo ~55.0.7` and `react 19.2.3`; CHANGELOG 1.2.0 confirms Expo 52→55, RN 0.74→0.84, React 18→19. `CLAUDE.md:33` also says "Expo 52 / React Native 0.74".
2. **Node version drift.** `README.md` says "Node.js v24 LTS" but `CONTRIBUTING.md` says "Node.js 24+". Node 24 is not currently LTS.
3. **API.md Endpoint 3 (Download) wrong response shape.** `docs/API.md:330-340` says download endpoint "Returns the audio file as a downloadable response." Actual code in `handle_download_request` returns JSON `{job_id, download_url, expires_in: 3600}` (pre-signed URL).
4. **API.md missing `/token` endpoint.** `lambda_handler.py:597-598, 704-756` exposes `POST /token?user_id=...` — undocumented.
5. **API.md missing `qa_transcript` request field.** `MeditationRequestModel` (`backend/src/models/requests.py:55`) supports `qa_transcript: List[QATranscriptItem]`; not in API.md.
6. **API.md summary response field `intensity` type drift.** Docs line 101 describe `intensity` as `string`; meditation request docs line 160 use `intensity: 0.8` (number).
7. **API.md "Invalid inference_type" error text drift.** Doc (lines 122-132) says `"inference_type must be 'summary' or 'meditation'"`; actual code `backend/src/models/requests.py:149-152` raises `Invalid inference_type: {inference_type}`.
8. **API.md job-status example responses** omit `streaming` / `download` / `generation_attempt` fields that `handle_job_status` actually returns.
9. **`docs/ARCHITECTURE.md` Technology Stack table** — same version drift as item 1.

### GAPS

1. **HLS streaming flow undocumented in ARCHITECTURE.md.** `hls_service.py`, `_process_meditation_hls`, playlist URL, streaming progress, `MAX_GENERATION_ATTEMPTS=3`. ARCHITECTURE mentions HLS only via "Audio: FFmpeg" bullet.
2. **Token/Gemini Live auth flow undocumented.** `_handle_token_request` implements per-user rate limiting, returns raw Gemini key as 60s token.
3. **`EXPO_PUBLIC_ANDROID_CLIENT_ID` undocumented.** Referenced in `frontend/components/AuthScreen.tsx:202` and `frontend/.env.example:11`; not in env tables.
4. **Backend `G_KEY` alias undocumented.** `settings.py` accepts `GEMINI_API_KEY` and legacy `G_KEY` via `AliasChoices`.
5. **Retry semantics undocumented.** `MAX_GENERATION_ATTEMPTS=3` and TTS fallback (Gemini→OpenAI) not described.
6. **Authorization check on job endpoints undocumented.** Docs say "no authentication"; code enforces user-id ownership (403 on mismatch).

### STALE

1. **`docs/README.md:142-172`** shows `tests/` as top-level dir with `tests/frontend/{unit,integration,e2e}`. Actual layout: `frontend/tests/{unit,integration,e2e}`.
2. **`README.md:21-26`** lists `tests/` as root dir — same stale post-migration.
3. **`CLAUDE.md` Architecture block** — same stale claim; tests live under `frontend/tests/`.
4. **`docs/README.md:84`** says `npm test` is "Run Jest (watch mode)" but `package.json` root script is `cd frontend && npx jest --forceExit` (no watch).

### BROKEN LINKS
None found. `README.md` → `docs/README.md`, `docs/README.md` → `API.md`/`ARCHITECTURE.md`, `docs/README.md` → `../banner.png` all resolve.

### STALE CODE EXAMPLES

1. **`docs/API.md:272-302`** — Client Usage polling loop doesn't handle the `streaming.playlist_url` field the code emits.
2. **`docs/API.md:385-425`** — Example 3 JS snippet treats meditation response as synchronous (`result.body.base64`). Actual `handle_meditation_request` returns `{job_id, status:"pending", ...}` — client must poll. Will not work if copy-pasted.

### CONFIG DRIFT

1. **`ENABLE_HLS_STREAMING` default** — `docs/README.md` says default `true`, code confirms. OK.
2. **Deploy parameter tables drift.** Root `README.md` and `docs/README.md` list different subsets (`IncludeDevOrigins`, `FfmpegLayerArn` in one; different fields in the other).

### STRUCTURE ISSUES

1. **Two README files duplicate environment/deployment content** (`/README.md` vs `/docs/README.md`) with drifted tables.
2. **`docs/` hierarchy claims vs reality.** `docs/README.md` implies only API/ARCHITECTURE; directory also has `docs/plans/*` not indexed.
3. **CLAUDE.md architecture section** duplicates ARCHITECTURE.md + README.md with its own drift.
