# Feedback Log

## Active Feedback

### PLAN_REVIEW - 2026-04-04 - Phase 2 Task Ordering and Type Placement

**Severity: Critical**

**Issue: Phase 2 Task 5 must come before Task 4, not after**

Task 4 (Integrate VoiceQA into MeditationControls) explicitly needs:
1. `getTransformedDict` exported from `BackendMeditationCall.tsx` (to pass sentiment data in `explore.tsx`)
1. `QATranscript` type (to type the `handleMeditationCall` parameter and payload)

Task 5 is where these exports are created. But Task 5 lists "Prerequisites: None" and Task 4 lists "Prerequisites: Tasks 2, 3". A zero-context engineer following task order will hit import errors in Task 4 because the exports do not exist yet.

**Fix:** Reorder Task 5 to come before Task 4 (renumber as Task 4, shift current Task 4 to Task 5). Update prerequisite references accordingly.

---

**Severity: Minor**

**Issue: QA types defined twice then moved -- unnecessary churn**

Task 1 defines `QAState`, `QAExchange`, `QATranscript` locally in `useGeminiLiveAPI.ts`. Task 5 then moves them to `frontend/types/api.ts` and updates imports. This creates a refactor step that could be avoided by defining the types in `types/api.ts` from the start in Task 1 (or in a dedicated Task 0-style setup task).

**Fix:** In Task 1, instruct the engineer to define the QA types in `frontend/types/api.ts` directly and import them in `useGeminiLiveAPI.ts`. Remove the type-move portion of Task 5 (keep only the `getTransformedDict` export portion).

---

**Severity: Minor**

**Issue: Phase 1 Task 5 shows full `to_dict()` replacement instead of incremental edit**

The implementation steps in Phase 1 Task 5 show the complete `to_dict()` method body as if it needs to be written from scratch. The method already exists with the exact same structure at line 87 of `requests.py`. An engineer might be confused about whether to replace or extend.

**Fix:** Change the instruction to say "Add the `qa_transcript` conditional to the existing `to_dict()` method after the `duration_minutes` line" and only show the lines to add, not the full method.

### FINAL_REVIEW - 2026-04-04 - Integration Bug and Minor Issues

**Severity: Critical (Implementation-level)**

**Issue: Field name mismatch between backend and frontend for token endpoint WebSocket URL**

The backend `/token` endpoint returns the Gemini Live API WebSocket URL as `"endpoint"`:
- `backend/src/handlers/lambda_handler.py` line 717: `"endpoint": "wss://generativelanguage.googleapis.com/ws/..."`

The frontend reads it as `"ws_url"`:
- `frontend/hooks/useGeminiLiveAPI.ts` line 86: `const { token, ws_url: wsUrl } = tokenData;`

This means `wsUrl` will be `undefined` at runtime, causing the WebSocket connection `${wsUrl}?key=${token}` to fail. The Q&A feature is non-functional as shipped.

The frontend test (`frontend/tests/unit/useGeminiLiveAPI-test.ts` line 105) mocks the response with `ws_url` which matches the frontend code but not the backend. The backend test (`backend/tests/unit/test_lambda_handler.py` line 634) correctly asserts `"endpoint"` in the body.

**Fix (Implementer):** Either change the backend to return `"ws_url"` instead of `"endpoint"`, or change the frontend to destructure `endpoint` instead of `ws_url`. Both sides and their respective tests must agree. The simplest fix is changing `useGeminiLiveAPI.ts` line 86 to `const { token, endpoint: wsUrl } = tokenData;` and updating the test mock at line 105 to use `endpoint` instead of `ws_url`.

**Route to:** Implementer

---

**Severity: Low (Implementation-level)**

**Issue: `MEDITATION_VOICE_INSTRUCTIONS` constant is dead code in `gemini_tts.py`**

The constant is defined at line 16 of `backend/src/providers/gemini_tts.py` but never used in any method. The plan (Phase 1 Task 2) specified adding voice style instructions to the API call, but only the constant definition was implemented -- it is not passed in the `generate_content` config.

**Fix (Implementer):** Either wire the instructions into the TTS API call (if the Gemini TTS model supports instruction text), or remove the unused constant and update the plan to document that the TTS model uses the voice name alone.

**Route to:** Implementer

---

**Severity: Low (Implementation-level)**

**Issue: Duplicated JSDoc comment in `frontend/types/api.ts`**

The comment `/** * Meditation result with streaming support */` appears at both line 59 and line 86. The first occurrence (line 59-60) is an orphaned copy left behind when the QA types were inserted before the `MeditationResult` interface.

**Fix (Implementer):** Remove lines 59-61 (the orphaned comment block).

**Route to:** Implementer

---

**Severity: Info (Documented limitation)**

**Issue: Gemini API key exposed to client via token endpoint**

The `/token` endpoint returns `settings.GEMINI_API_KEY` directly to the client. This is acknowledged in the code (line 712 TODO), ADR-2 in Phase-0.md, and the Phase 1 known limitations section. This is acceptable for MVP but should be tracked for replacement with ephemeral tokens.

**No action required** -- documented and accepted.

## Resolved Feedback
