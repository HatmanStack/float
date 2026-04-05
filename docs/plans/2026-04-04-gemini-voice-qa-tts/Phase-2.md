# Phase 2: Frontend Voice Q&A and Transcript Integration

## Phase Goal

Implement the client-side Gemini Live API voice Q&A experience in the React Native frontend.
When a user taps Generate, a short voice conversation (2-3 exchanges) begins between the user
and a Gemini-powered agent that uses the selected floats' sentiment data. The transcript is
captured and sent with the meditation request. A text fallback is provided when microphone
permission is denied. The meditation request payload is updated to include the transcript.

### Success Criteria

- Tapping Generate starts a voice Q&A session via Gemini Live API WebSocket
- The Q&A agent asks 1-2 targeted questions based on selected float sentiment data
- Audio plays back the agent's responses through the device speaker
- The conversation transcript is captured and displayed inline
- After Q&A completes, meditation generation proceeds with the transcript included
- Text fallback works when microphone permission is denied
- Skip Q&A option available (user can bypass and go straight to meditation)
- Frontend tests pass for Q&A flow, text fallback, and skip behavior

### Estimated Tokens

~45,000

## Prerequisites

- Phase 1 must be complete (token endpoint, qa_transcript in request model)
- `expo-av` is already a dependency (used by RecordButton for mic access)
- Device/emulator with microphone access for manual testing

## Tasks

### Task 1: Create Gemini Live API Service Hook

**Goal:** Create a custom React hook that manages the WebSocket connection to the Gemini
Live API, handles audio streaming (send mic input, receive agent audio), and captures the
text transcript of the conversation.

**Files to Create:**

- `frontend/hooks/useGeminiLiveAPI.ts` - Custom hook for Live API connection

**Prerequisites:** Phase 1 Task 6 (token endpoint exists)

**Implementation Steps:**

1. Create `frontend/hooks/useGeminiLiveAPI.ts`. This hook manages:
   - Token fetching from the backend `/token` endpoint
   - WebSocket connection to the Gemini Live API
   - Sending audio data from the microphone
   - Receiving audio data and text from the model
   - Tracking conversation state (connecting, listening, processing, responding, complete)
   - Building the transcript array

1. The hook interface should be:

   ```typescript
   interface UseGeminiLiveAPIOptions {
     sentimentData: TransformedDict;  // Float sentiment data for system prompt
     onTranscriptComplete: (transcript: QATranscript) => void;
     onError: (error: Error) => void;
   }

   interface UseGeminiLiveAPIReturn {
     state: QAState;  // 'idle' | 'connecting' | 'listening' | 'processing' | 'responding' | 'complete'
     transcript: QAExchange[];
     startSession: () => Promise<void>;
     endSession: () => void;
     sendAudioChunk: (chunk: ArrayBuffer) => void;
     sendTextMessage: (text: string) => void;  // For text fallback
   }
   ```

1. Define the types at the top of the file:

   ```typescript
   export type QAState = 'idle' | 'connecting' | 'listening' | 'processing' | 'responding' | 'complete';

   export interface QAExchange {
     role: 'assistant' | 'user';
     text: string;
   }

   export type QATranscript = QAExchange[];
   ```

1. The `startSession` function should:
   - Fetch a token from `${LAMBDA_URL}/token?user_id=${userId}`
   - Open a WebSocket to the endpoint returned in the token response
   - Send the initial setup message with a system prompt that includes the float sentiment
     data. The system prompt should instruct the model to:
     - Act as a compassionate meditation guide doing a brief check-in
     - Reference specific incidents from the sentiment data
     - Ask 1-2 targeted questions about how the user is feeling
     - Keep the conversation to 2-3 total exchanges
     - End by saying something like "Thank you for sharing. Let me create a meditation
       tailored to what you've told me."
   - Set state to `'listening'` once the connection is established

1. Handle WebSocket messages:
   - Text responses from the model: add to transcript, set state to `'responding'`
   - Audio responses: play through device speaker using `expo-av` Audio
   - End-of-turn signals: set state back to `'listening'`
   - Session end: set state to `'complete'`, call `onTranscriptComplete`

1. Track exchange count. After the model's second or third response, automatically end the
   session and transition to `'complete'`.

1. Handle cleanup: close WebSocket on unmount, stop audio playback, release mic resources.

1. The Lambda URL comes from `process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL`. Import or
   reference it consistently with `BackendMeditationCall.tsx`.

**Verification Checklist:**

- [x] Hook exports `useGeminiLiveAPI` as default
- [x] All types (`QAState`, `QAExchange`, `QATranscript`) are exported
- [x] `startSession` fetches token and opens WebSocket
- [x] Transcript accumulates exchanges from both sides
- [x] Session auto-ends after 2-3 exchanges
- [x] Cleanup closes WebSocket and stops audio
- [x] `sendTextMessage` works for text fallback mode

**Testing Instructions:**

Create `frontend/tests/unit/useGeminiLiveAPI-test.ts`:

1. `test_initial_state_is_idle` - Render hook, assert `state` is `'idle'` and `transcript`
   is empty.
1. `test_start_session_fetches_token` - Mock `fetch` to return token response. Call
   `startSession()`. Assert fetch was called with `/token` URL.
1. `test_start_session_opens_websocket` - Mock `WebSocket` global. Call `startSession()`.
   Assert WebSocket constructor was called with the endpoint URL.
1. `test_transcript_accumulates_exchanges` - Simulate WebSocket messages for assistant
   text. Assert transcript contains the exchange.
1. `test_session_ends_after_max_exchanges` - Simulate enough exchanges. Assert state
   becomes `'complete'` and `onTranscriptComplete` is called.
1. `test_cleanup_closes_websocket` - Call `endSession()`. Assert WebSocket `close()` is called.
1. `test_send_text_message` - Call `sendTextMessage("hello")`. Assert WebSocket `send()`
   is called with the message.
1. `test_error_handling` - Mock `fetch` to reject. Call `startSession()`. Assert
   `onError` is called.

Mock WebSocket as a class with `send`, `close`, and event handler properties (`onopen`,
`onmessage`, `onerror`, `onclose`). Mock `fetch` for the token endpoint.

```bash
npm test -- --testPathPattern="useGeminiLiveAPI"
```

**Commit Message Template:**

```text
feat(frontend): add Gemini Live API hook for voice Q&A

- Create useGeminiLiveAPI hook with WebSocket management
- Handle token exchange, audio streaming, transcript capture
- Auto-end session after 2-3 exchanges
- Add comprehensive unit tests
```

---

### Task 2: Create Voice Q&A UI Component

**Goal:** Create an inline UI component that replaces the Generate button during the Q&A
conversation. It shows mic status, visual feedback, transcript display, and a skip button.

**Files to Create:**

- `frontend/components/ScreenComponents/VoiceQA.tsx` - Voice Q&A UI component

**Prerequisites:** Task 1 (useGeminiLiveAPI hook)

**Implementation Steps:**

1. Create `frontend/components/ScreenComponents/VoiceQA.tsx`. This component renders inline
   in the same space as the Generate button (same parent container in MeditationControls).

1. Props interface:

   ```typescript
   interface VoiceQAProps {
     sentimentData: TransformedDict;
     onComplete: (transcript: QATranscript) => void;
     onSkip: () => void;
     onError: (error: Error) => void;
   }
   ```

1. The component should:
   - Use the `useGeminiLiveAPI` hook internally
   - Auto-start the session on mount (call `startSession()` in a `useEffect`)
   - Display different UI based on the Q&A state:
     - `connecting`: Show "Connecting..." with `ActivityIndicator`
     - `listening`: Show a pulsing mic icon (use `MaterialIcons` "mic" icon with animated
       opacity). Show text "Listening..."
     - `processing`: Show "Thinking..." with `ActivityIndicator`
     - `responding`: Show a speaker icon. Show the assistant's current text response
     - `complete`: Briefly show "Starting meditation..." then call `onComplete`
   - Display the transcript as it builds (scrollable list of exchanges)
   - Show a "Skip" button (small, bottom-right) that calls `onSkip` to bypass Q&A

1. Style the component to fit in the same space as the Generate button area. Use the app's
   existing style patterns:
   - `Colors['buttonPressed']` and `Colors['buttonUnpressed']` for interactive elements
   - `ThemedText` and `ThemedView` for themed components
   - `useStyles()` for shared styles

1. Handle the microphone permission flow:
   - Use `Audio.requestPermissionsAsync()` from `expo-av` (same pattern as RecordButton)
   - If permission granted, proceed with voice Q&A
   - If permission denied, switch to text input mode (Task 3)

1. For audio recording (sending mic input to Live API):
   - Use `Audio.Recording` from `expo-av` to capture microphone input
   - Configure recording for the format expected by Gemini Live API (PCM 16-bit, 16kHz)
   - Stream audio chunks to the hook's `sendAudioChunk` method
   - The exact recording configuration depends on `expo-av` capabilities; reference
     `RecordButton.tsx` for the existing pattern

**Verification Checklist:**

- [x] Component renders without errors
- [x] Shows appropriate UI for each Q&A state
- [x] Transcript displays as exchanges accumulate
- [x] Skip button calls `onSkip`
- [x] Mic permission is requested on mount
- [x] Pulsing animation works during listening state
- [x] Component cleans up (stops recording, closes session) on unmount

**Testing Instructions:**

Create `frontend/tests/unit/VoiceQA-test.tsx`:

1. `test_renders_connecting_state` - Mock `useGeminiLiveAPI` to return `state: 'connecting'`.
   Render component. Assert "Connecting" text is visible.
1. `test_renders_listening_state` - Mock hook with `state: 'listening'`. Assert mic icon
   is visible.
1. `test_renders_transcript` - Mock hook with transcript containing exchanges. Assert
   exchange text is visible.
1. `test_skip_button_calls_onSkip` - Render component. Press Skip button. Assert `onSkip`
   was called.
1. `test_calls_onComplete_when_session_ends` - Mock hook to transition to `'complete'`.
   Assert `onComplete` is called with the transcript.
1. `test_requests_mic_permission` - Mock `Audio.requestPermissionsAsync`. Render component.
   Assert permission was requested.

Mock the `useGeminiLiveAPI` hook by mocking the module:

```typescript
jest.mock('@/hooks/useGeminiLiveAPI', () => ({
  __esModule: true,
  default: jest.fn(),
}));
```

```bash
npm test -- --testPathPattern="VoiceQA"
```

**Commit Message Template:**

```text
feat(frontend): add VoiceQA component for inline Q&A UI

- Create VoiceQA component with state-driven UI
- Show mic icon, transcript, and skip button
- Handle microphone permission flow
- Add unit tests for all Q&A states
```

---

### Task 3: Add Text Fallback for Mic Denial

**Goal:** When microphone permission is denied, the VoiceQA component switches to a text
input mode where the user types responses instead of speaking.

**Files to Modify:**

- `frontend/components/ScreenComponents/VoiceQA.tsx` - Add text input fallback mode

**Prerequisites:** Task 2 (VoiceQA component exists)

**Implementation Steps:**

1. Add a `textMode` state to the VoiceQA component. Set it to `true` when
   `Audio.requestPermissionsAsync()` returns `{ granted: false }`.

1. When in text mode:
   - Instead of the mic icon, show a `TextInput` component for the user to type
   - Show a "Send" button next to the input
   - When the user taps Send, call `sendTextMessage(text)` from the hook
   - Clear the input after sending
   - The assistant's responses are still shown as text (no audio playback needed in text mode)
   - The conversation flow (2-3 exchanges, auto-end) works the same way

1. The `startSession` call in text mode should still happen -- the WebSocket connection
   works the same way. The difference is only in input modality (text instead of audio).

1. Show a brief message when switching to text mode: "Microphone not available. You can
   type your responses instead."

**Verification Checklist:**

- [x] Text mode activates when mic permission is denied
- [x] TextInput is visible in text mode
- [x] Send button sends text via `sendTextMessage`
- [x] Assistant responses display as text
- [x] Transcript captures text exchanges
- [x] "Microphone not available" message is shown

**Testing Instructions:**

Add tests to `frontend/tests/unit/VoiceQA-test.tsx`:

1. `test_text_mode_on_mic_denial` - Mock `Audio.requestPermissionsAsync` to return
   `{ granted: false }`. Render component. Assert TextInput is visible.
1. `test_text_mode_send_button` - In text mode, type text and press Send. Assert
   `sendTextMessage` was called with the text.
1. `test_text_mode_shows_message` - Assert "Microphone not available" text is visible.
1. `test_text_mode_transcript` - Simulate exchanges in text mode. Assert transcript
   displays correctly.

```bash
npm test -- --testPathPattern="VoiceQA"
```

**Commit Message Template:**

```text
feat(frontend): add text fallback for mic denial in VoiceQA

- Switch to text input mode when microphone permission denied
- Show TextInput and Send button for typed responses
- Display fallback message to user
- Add tests for text mode behavior
```

---

### Task 4: Integrate VoiceQA into MeditationControls

**Goal:** Wire the VoiceQA component into the existing MeditationControls component so that
tapping Generate starts the Q&A flow, and after Q&A completes, meditation generation proceeds
with the transcript.

**Files to Modify:**

- `frontend/components/ScreenComponents/MeditationControls.tsx` - Add Q&A state and VoiceQA
- `frontend/components/BackendMeditationCall.tsx` - Accept and send `qa_transcript` in payload
- `frontend/app/(tabs)/explore.tsx` - Pass sentiment data to MeditationControls

**Prerequisites:** Tasks 2, 3 (VoiceQA component is complete)

**Implementation Steps:**

1. **Update MeditationControls props and state:**

   Add new props to `MeditationControlsProps`:

   ```typescript
   sentimentData?: TransformedDict;  // For Q&A system prompt
   ```

   Add state for Q&A flow:

   ```typescript
   const [qaActive, setQaActive] = useState(false);
   const [qaTranscript, setQaTranscript] = useState<QATranscript | null>(null);
   ```

1. **Modify the Generate button behavior:**

   Currently, pressing Generate calls `handleMeditationCall(selectedDuration)`. Change this:
   - When Generate is pressed, set `qaActive = true` instead of calling meditation directly
   - This renders the VoiceQA component in place of the Generate button

1. **Add VoiceQA rendering:**

   In the "No content yet" section (the Generate button block, around line 307), add a
   conditional:

   ```typescript
   if (qaActive) {
     return (
       <VoiceQA
         sentimentData={sentimentData}
         onComplete={(transcript) => {
           setQaTranscript(transcript);
           setQaActive(false);
           handleMeditationCall(selectedDuration);  // Now with transcript
         }}
         onSkip={() => {
           setQaActive(false);
           handleMeditationCall(selectedDuration);  // Without transcript
         }}
         onError={(error) => {
           console.error('Q&A error:', error);
           setQaActive(false);
           handleMeditationCall(selectedDuration);  // Fall back to normal flow
         }}
       />
     );
   }
   ```

1. **Pass transcript to meditation call:**

   Update `MeditationControlsProps` to accept a callback that can receive the transcript:

   ```typescript
   handleMeditationCall: (durationMinutes: number, qaTranscript?: QATranscript) => void;
   ```

   Update the VoiceQA `onComplete` to pass the transcript:

   ```typescript
   onComplete={(transcript) => {
     setQaActive(false);
     handleMeditationCall(selectedDuration, transcript);
   }}
   ```

1. **Update BackendMeditationCallStreaming:**

   In `frontend/components/BackendMeditationCall.tsx`, add an optional `qaTranscript`
   parameter to `BackendMeditationCallStreaming`:

   ```typescript
   export async function BackendMeditationCallStreaming(
     selectedIndexes: number[],
     resolvedIncidents: IncidentData[],
     musicList: string[],
     userId: string,
     lambdaUrl: string = LAMBDA_FUNCTION_URL,
     onStatusUpdate?: (status: JobStatusResponse) => void,
     durationMinutes: number = 5,
     signal?: AbortSignal,
     qaTranscript?: QATranscript  // NEW
   ): Promise<StreamingMeditationResponse> {
   ```

   In the payload construction (around line 243), add the transcript:

   ```typescript
   const payload = {
     inference_type: 'meditation',
     audio: 'NotAvailable',
     prompt: 'NotAvailable',
     music_list: musicList,
     input_data: dict,
     user_id: userId,
     duration_minutes: durationMinutes,
     ...(qaTranscript && { qa_transcript: qaTranscript }),
   };
   ```

1. **Update explore.tsx:**

   In `explore.tsx`, the `useMeditation` hook needs to:
   - Accept and forward `qaTranscript` to `BackendMeditationCallStreaming`
   - Update `handleMeditationCall` to accept an optional transcript parameter
   - Pass the sentiment data down to `MeditationControls` via a new prop

   The `getTransformedDict` function is already in `BackendMeditationCall.tsx`. To get the
   sentiment data for the Q&A system prompt, export it or create a similar transform in
   explore.tsx. The simplest approach: export `getTransformedDict` from
   `BackendMeditationCall.tsx` and call it in explore.tsx to prepare the data.

   Add a `sentimentData` prop to `MeditationControls`:

   ```typescript
   <MeditationControls
     ...existing props...
     sentimentData={getTransformedDict(incidentList, selectedIndexes)}
   />
   ```

**Verification Checklist:**

- [x] Tapping Generate shows VoiceQA component
- [x] After Q&A completes, meditation generation starts with transcript
- [x] Skip button bypasses Q&A and starts meditation without transcript
- [x] Q&A errors fall back to normal meditation generation
- [x] Transcript is included in the meditation request payload
- [x] `BackendMeditationCallStreaming` sends `qa_transcript` when provided
- [x] Existing meditation flow (without Q&A) still works

**Testing Instructions:**

Update `frontend/tests/unit/MeditationControls-test.tsx`:

1. `test_generate_shows_voice_qa` - Render MeditationControls with sentiment data. Press
   Generate. Assert VoiceQA component is rendered (mock VoiceQA module).
1. `test_qa_complete_triggers_meditation` - Simulate VoiceQA `onComplete` callback. Assert
   `handleMeditationCall` was called.
1. `test_skip_qa_triggers_meditation` - Simulate VoiceQA `onSkip` callback. Assert
   `handleMeditationCall` was called without transcript.
1. `test_qa_error_falls_back` - Simulate VoiceQA `onError` callback. Assert
   `handleMeditationCall` was called.

Update `frontend/tests/unit/BackendMeditationCall-test.tsx`:

1. `test_payload_includes_qa_transcript` - Call `BackendMeditationCallStreaming` with a
   `qaTranscript` parameter. Assert the fetch payload includes `qa_transcript`.
1. `test_payload_omits_qa_transcript_when_undefined` - Call without transcript. Assert
   payload does not include `qa_transcript`.

```bash
npm test -- --testPathPattern="MeditationControls|BackendMeditationCall"
```

**Commit Message Template:**

```text
feat(frontend): integrate VoiceQA into meditation generation flow

- Wire VoiceQA into MeditationControls with Generate button override
- Pass Q&A transcript through to BackendMeditationCallStreaming
- Add sentimentData prop for Q&A system prompt
- Update explore.tsx to provide sentiment data
- Add tests for Q&A integration and payload
```

---

### Task 5: Export getTransformedDict and Add QA Types

**Goal:** Export shared types and the `getTransformedDict` utility from
`BackendMeditationCall.tsx` so they can be used by explore.tsx and VoiceQA without
duplication.

**Files to Modify:**

- `frontend/components/BackendMeditationCall.tsx` - Export `getTransformedDict` and
  `TransformedDict` type
- `frontend/types/api.ts` - Add Q&A-related types (or create new type file)

**Prerequisites:** None (can be done early in the phase)

**Implementation Steps:**

1. In `frontend/components/BackendMeditationCall.tsx`:
   - Change `getTransformedDict` from `const` to `export const`
   - Export the `TransformedDict` interface and `IncidentData` interface

1. Add Q&A types. Decide whether to put them in `frontend/types/api.ts` or a new
   `frontend/types/qa.ts`. Since they are closely related to the API flow, `api.ts` is
   reasonable. Add:

   ```typescript
   export type QAState = 'idle' | 'connecting' | 'listening' | 'processing' | 'responding' | 'complete';

   export interface QAExchange {
     role: 'assistant' | 'user';
     text: string;
   }

   export type QATranscript = QAExchange[];
   ```

   Then import these types in `useGeminiLiveAPI.ts` and `VoiceQA.tsx` instead of defining
   them locally.

**Verification Checklist:**

- [x] `getTransformedDict` is exported from `BackendMeditationCall.tsx`
- [x] `TransformedDict` and `IncidentData` types are exported
- [x] Q&A types are defined in `frontend/types/api.ts`
- [x] No duplicate type definitions across files
- [x] Existing imports of `BackendMeditationCall` still work

**Testing Instructions:**

Existing tests should still pass:

```bash
npm test -- --testPathPattern="BackendMeditationCall"
```

**Commit Message Template:**

```text
refactor(frontend): export shared types and utility for Q&A integration

- Export getTransformedDict, TransformedDict, IncidentData from BackendMeditationCall
- Add QAState, QAExchange, QATranscript types to types/api.ts
```

---

### Task 6: End-to-End Integration Test

**Goal:** Add an integration test that exercises the full Q&A-to-meditation flow with mocked
APIs, verifying that the transcript flows from the Q&A through to the meditation request.

**Files to Create:**

- `frontend/tests/integration/voice-qa-flow-test.tsx` - Integration test for Q&A flow

**Prerequisites:** Tasks 1-5 (all Q&A components and integration are complete)

**Implementation Steps:**

1. Create `frontend/tests/integration/voice-qa-flow-test.tsx`. This test:
   - Renders the explore tab screen (or the relevant component subtree)
   - Mocks the backend `/token` endpoint
   - Mocks the WebSocket class for the Gemini Live API
   - Mocks the meditation request endpoint
   - Simulates the full flow: select floats, tap Generate, complete Q&A, verify meditation
     request includes transcript

1. Follow the pattern of existing integration tests like
   `frontend/tests/integration/meditation-flow-test.tsx`.

1. Key assertions:
   - Token endpoint is called when Generate is tapped
   - WebSocket connection is established
   - After simulated Q&A exchanges, meditation request is sent
   - Meditation request payload includes `qa_transcript` with the exchanges
   - Skip button sends meditation request without `qa_transcript`

**Verification Checklist:**

- [x] Integration test passes
- [x] Test covers the happy path (Q&A to meditation with transcript)
- [x] Test covers the skip path (no transcript)
- [x] Test covers the error path (Q&A fails, meditation proceeds without transcript)

**Testing Instructions:**

```bash
npm test -- --testPathPattern="voice-qa-flow"
```

**Commit Message Template:**

```text
test(frontend): add integration test for voice Q&A to meditation flow

- Test full Q&A flow with mocked WebSocket and backend APIs
- Cover happy path, skip path, and error fallback
- Verify transcript inclusion in meditation request payload
```

## Phase Verification

After completing all tasks, verify the entire phase:

1. **All frontend tests pass:**

   ```bash
   npm test
   ```

1. **Frontend lint passes:**

   ```bash
   npm run lint
   ```

1. **All backend tests still pass:**

   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   ```

1. **Full check passes:**

   ```bash
   npm run check
   ```

1. **Manual verification (optional, not required for CI):**
   - Run `npm start` and test on device/emulator
   - Verify Generate button starts Q&A
   - Verify Skip bypasses Q&A
   - Verify text mode works when mic is denied

### Known Limitations

- The Gemini Live API WebSocket protocol specifics (message format, setup message structure)
  may differ from what is documented. The engineer should consult the latest Gemini Live API
  docs and `google-genai` SDK source during implementation
- Audio recording format compatibility between `expo-av` and Gemini Live API needs to be
  verified during implementation. PCM 16-bit 16kHz is the expected format but may need
  adjustment
- React Native WebSocket may have platform-specific quirks with binary data. If issues arise
  on specific platforms, document them and consider platform-specific implementations
  (similar to the existing `useHLSPlayer.ts` / `useHLSPlayer.web.ts` pattern)
- The Q&A agent's system prompt may need tuning based on real usage. The initial prompt in
  this plan is a starting point
- Audio playback of agent responses during Q&A uses `expo-av`. If latency is too high for
  streaming audio, a web-based fallback (similar to HLS player web implementation) may be
  needed
