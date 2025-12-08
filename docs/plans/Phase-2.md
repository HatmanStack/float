# Phase 2: Frontend HLS Playback

## Phase Goal

Implement client-side HLS streaming playback across all platforms. The frontend will use HLS.js on web and WebView-wrapped HLS.js on mobile to provide a unified streaming experience. Users will see playback begin within seconds of starting meditation generation, with an option to download the complete MP3 after streaming finishes.

**Success Criteria**:
- HLS.js plays streaming audio on web browsers
- WebView-based HLS.js player works on iOS and Android
- Playback starts within 5 seconds of job creation
- Download button appears after streaming completes
- Download triggers MP3 generation and file save
- Error states handled gracefully with retry options
- All unit tests pass with mocked HLS.js and fetch

**Estimated Tokens**: ~70,000

---

## Prerequisites

- Phase 1 complete (backend HLS generation working)
- Backend deployed with HLS streaming enabled
- Understanding of existing audio playback in `MeditationControls.tsx`
- Understanding of API client in `BackendMeditationCall.tsx`

---

## Tasks

### Task 1: Add HLS.js and WebView Dependencies

**Goal**: Install required npm packages for HLS playback across platforms.

**Files to Modify/Create**:
- `frontend/package.json` - Add dependencies
- `package.json` (root) - Verify workspace config

**Prerequisites**:
- None (first task)

**Implementation Steps**:

1. Add HLS.js for web playback:
   - Package: `hls.js` version ^1.5.0
   - This provides HLS parsing and playback for browsers without native support

2. Add WebView for mobile HLS:
   - Package: `react-native-webview` version ^13.0.0
   - Required for embedding HLS.js player on mobile platforms

3. Verify Expo compatibility:
   - Check expo-compatible versions of react-native-webview
   - May need to use expo-specific installation: `npx expo install react-native-webview`

4. Update type definitions if needed:
   - HLS.js includes TypeScript types
   - WebView types included in package

5. Run install and verify no peer dependency conflicts:
   - Run `npm install` from project root
   - Verify no errors or warnings

**Verification Checklist**:
- [x] `hls.js` installed in frontend
- [x] `react-native-webview` installed in frontend
- [x] No peer dependency conflicts
- [x] TypeScript types available

**Testing Instructions**:

No unit tests for dependency installation. Verify via:
```bash
cd frontend && npm ls hls.js react-native-webview
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

chore(frontend): add HLS playback dependencies

Add hls.js for web HLS playback
Add react-native-webview for mobile HLS player
```

---

### Task 2: Create HLS Player Hook for Web

**Goal**: Implement a React hook that manages HLS.js playback on web platform.

**Files to Create**:
- `frontend/hooks/useHLSPlayer.ts` - Native mobile stub (returns null/no-op, actual playback via WebView component)
- `frontend/hooks/useHLSPlayer.web.ts` - Web-specific implementation with HLS.js (Metro bundler resolves `.web.ts` for web builds)
- `frontend/hooks/index.ts` - Export hook (directory exists with `useColorScheme.ts`, `useColorScheme.web.ts`, `useThemeColor.ts`)
- `tests/frontend/unit/useHLSPlayer-test.tsx` - Unit tests (use `.tsx` extension to match project convention)

**Prerequisites**:
- Task 1 complete (dependencies installed)

**Implementation Steps**:

1. Define hook interface:
   ```typescript
   interface HLSPlayerState {
     isLoading: boolean;
     isPlaying: boolean;
     isComplete: boolean;
     error: Error | null;
     duration: number | null;
     currentTime: number;
   }

   interface HLSPlayerControls {
     play: () => void;
     pause: () => void;
     seek: (time: number) => void;
     retry: () => void;
   }

   function useHLSPlayer(playlistUrl: string | null): [HLSPlayerState, HLSPlayerControls]
   ```

2. Create web implementation (`useHLSPlayer.web.ts`):
   - Import HLS.js
   - Create audio element on mount
   - Initialize HLS.js when playlistUrl provided
   - Handle HLS events:
     - `MANIFEST_PARSED`: Ready to play, call play()
     - `FRAG_LOADED`: Track progress
     - `ERROR`: Handle errors (fatal vs recoverable)
     - `LEVEL_LOADED`: Get duration when available

3. Implement state management:
   - Track loading state during initialization
   - Track playing state via audio element events
   - Track completion via `ended` event
   - Track errors from HLS.js

4. Implement controls:
   - `play`: Call audio.play() if loaded
   - `pause`: Call audio.pause()
   - `seek`: Set audio.currentTime
   - `retry`: Destroy HLS instance, reinitialize

5. Handle Safari native HLS:
   - Check `audio.canPlayType('application/vnd.apple.mpegurl')`
   - If supported, set audio.src directly (no HLS.js needed)
   - Same interface, different implementation path

6. Cleanup on unmount:
   - Destroy HLS instance
   - Remove audio element
   - Clear all event listeners

7. Handle live playlist behavior:
   - HLS.js automatically polls live playlists
   - Configure `liveSyncDuration` for appropriate buffering
   - Handle transition from live to VOD when `#EXT-X-ENDLIST` appears

**Verification Checklist**:
- [x] Hook initializes HLS.js on web platform
- [x] Playback starts after manifest parsed
- [x] State updates correctly during playback
- [x] Controls work (play, pause, seek)
- [x] Safari native HLS fallback works
- [x] Cleanup on unmount
- [x] Error handling works

**Testing Instructions**:

Unit tests to write:
- Test hook initialization with null URL (no-op)
- Test hook initialization with valid URL
- Test state transitions (loading → playing → complete)
- Test error state handling
- Test control functions
- Test cleanup on unmount

Mocking required:
- Mock HLS.js constructor and methods
- Mock HTMLAudioElement
- Mock canPlayType for Safari detection

Run tests:
```bash
npm test -- --testPathPattern="useHLSPlayer"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): add useHLSPlayer hook for web HLS playback

Implement HLS.js integration for streaming audio
Handle Safari native HLS fallback
Add playback controls and state management
```

---

### Task 3: Create HLS Player Component for Mobile (WebView)

**Goal**: Implement a React Native component that uses WebView to play HLS audio on mobile platforms.

**Files to Create**:
- `frontend/components/HLSPlayer/HLSPlayer.tsx` - Mobile WebView player
- `frontend/components/HLSPlayer/HLSPlayer.web.tsx` - Web version (uses hook)
- `frontend/components/HLSPlayer/index.ts` - Platform-specific export
- `frontend/components/HLSPlayer/hlsPlayerHtml.ts` - HTML template as exported string constant (Metro doesn't bundle raw HTML files; embed as template literal)
- `tests/frontend/unit/HLSPlayer-test.tsx` - Unit tests

**Prerequisites**:
- Task 2 complete (web hook ready)

**Implementation Steps**:

1. Create component interface:
   ```typescript
   interface HLSPlayerProps {
     playlistUrl: string | null;
     onPlaybackStart?: () => void;
     onPlaybackComplete?: () => void;
     onError?: (error: Error) => void;
     autoPlay?: boolean;
   }
   ```

2. Create HTML template as TypeScript string (`hlsPlayerHtml.ts`):
   - Export as template literal: `export const hlsPlayerHtml = \`<!DOCTYPE html>...\`;`
   - Metro bundler cannot handle raw .html files; embedding as string is the standard approach
   - Include HLS.js from CDN (unpkg or cdnjs) in a script tag
   - Create audio element
   - Initialize HLS.js with playlist URL from postMessage
   - Send events back to React Native via `window.ReactNativeWebView.postMessage(JSON.stringify({...}))`:
     - `{type: 'ready'}`
     - `{type: 'playing'}`
     - `{type: 'paused'}`
     - `{type: 'complete'}`
     - `{type: 'error', message: '...'}`
     - `{type: 'timeupdate', currentTime: N, duration: N}`
   - Receive commands via `document.addEventListener('message', ...)`:
     - `{command: 'play'}`
     - `{command: 'pause'}`
     - `{command: 'seek', time: N}`
     - `{command: 'load', url: '...'}`

3. Create mobile component implementation:
   - Use react-native-webview
   - Load HTML template
   - Inject playlist URL via postMessage after load
   - Handle messages from WebView for state updates
   - Expose controls via ref or callbacks

4. Create web component implementation:
   - Simple wrapper around useHLSPlayer hook
   - Render hidden audio element
   - Expose same interface as mobile version

5. Create platform-specific exports:
   - `index.ts` exports based on Platform.OS
   - Or use `.native.tsx` / `.web.tsx` file extensions

6. Handle WebView-specific considerations:
   - Set `allowsInlineMediaPlayback` for iOS
   - Set `mediaPlaybackRequiresUserAction` to false for autoplay
   - Handle audio focus on Android

7. Style WebView:
   - Make it invisible (height: 0, opacity: 0)
   - Audio-only, no video display needed

**Verification Checklist**:
- [x] WebView loads HLS.js successfully
- [x] Playlist URL injected and playback starts
- [x] State updates propagate to React Native
- [x] Controls work via postMessage
- [x] Works on iOS simulator/device
- [x] Works on Android emulator/device
- [x] Web version works in browser

**Testing Instructions**:

Unit tests to write:
- Test component renders WebView on mobile
- Test postMessage communication
- Test state updates from WebView messages
- Test control commands sent to WebView

Mocking required:
- Mock react-native-webview
- Mock Platform.OS for platform testing
- Mock postMessage handlers

Run tests:
```bash
npm test -- --testPathPattern="HLSPlayer"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): add HLSPlayer component with WebView for mobile

Create WebView-based HLS player for iOS/Android
Add platform-specific implementations
Handle bidirectional postMessage communication
```

---

### Task 4: Update API Client for Streaming Jobs

**Goal**: Modify BackendMeditationCall to handle streaming job responses and provide playlist URLs.

**Files to Create**:
- `frontend/types/api.ts` - Add streaming types (create `frontend/types/` directory first - does not exist)

**Files to Modify**:
- `frontend/components/BackendMeditationCall.tsx` - Update for streaming support
- `tests/frontend/unit/BackendMeditationCall-test.tsx` - Update tests

**Prerequisites**:
- Understanding of current polling implementation

**Implementation Steps**:

1. Define new response types:
   ```typescript
   interface StreamingInfo {
     playlist_url: string;
     segments_completed: number;
     segments_total: number | null;
   }

   interface DownloadInfo {
     available: boolean;
     url: string | null;
   }

   interface JobStatusResponse {
     job_id: string;
     status: 'pending' | 'processing' | 'streaming' | 'completed' | 'failed';
     streaming?: StreamingInfo;
     download?: DownloadInfo;
     error?: { code: string; message: string };
   }
   ```

2. Update poll response handling:
   - Detect `streaming` field in response
   - When status becomes `streaming`, return playlist URL immediately
   - Continue polling in background for completion
   - Return both playlist URL and completion promise

3. Modify return type of meditation call:
   ```typescript
   interface MeditationResult {
     // Existing (for base64 fallback)
     meditationUri?: string;
     musicList?: string[];

     // New (for streaming)
     playlistUrl?: string;
     isStreaming: boolean;
     waitForCompletion: () => Promise<void>;
     getDownloadUrl: () => Promise<string>;
   }
   ```

4. Implement streaming-aware polling:
   - Poll until status is `streaming` OR `completed`
   - If streaming, return early with playlist URL
   - Provide `waitForCompletion` function that continues polling
   - `getDownloadUrl` calls download endpoint after completion

5. Add download endpoint call:
   - POST to `/job/{job_id}/download?user_id={userId}`
   - Returns `{ download_url: string, expires_in: number }`
   - Handle errors (job not complete, generation failed)

6. Maintain backward compatibility:
   - Check for `streaming` field presence
   - If absent, use existing base64 flow
   - Return consistent interface regardless of mode

**Verification Checklist**:
- [x] Streaming jobs detected correctly
- [x] Playlist URL returned when streaming starts
- [x] Background polling continues after streaming starts
- [x] Download URL fetched successfully
- [x] Backward compatible with base64 responses
- [x] Error handling for all new paths

**Testing Instructions**:

Unit tests to write:
- Test streaming job detection
- Test early return with playlist URL
- Test background completion polling
- Test download URL fetch
- Test backward compatibility with base64
- Test error handling

Mocking required:
- Mock fetch for API responses
- Mock sequential responses (pending → streaming → completed)

Run tests:
```bash
npm test -- --testPathPattern="BackendMeditationCall"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): update API client for HLS streaming support

Add streaming job response handling
Return playlist URL when streaming begins
Add download URL fetch capability
Maintain backward compatibility with base64 mode
```

---

### Task 5: Update Meditation Controls for Streaming

**Goal**: Modify MeditationControls component to use HLS player when streaming is available.

**Files to Modify/Create**:
- `frontend/components/ScreenComponents/MeditationControls.tsx` - Integrate HLS player
- `tests/frontend/unit/MeditationControls-test.tsx` - Update tests (create if not exists)

**Prerequisites**:
- Task 3 complete (HLSPlayer component ready)
- Task 4 complete (API client updated)

**Implementation Steps**:

1. Update component to accept streaming props:
   - Add `playlistUrl` prop
   - Add `isStreaming` prop
   - Add `onDownloadRequest` callback

2. Conditional rendering based on mode:
   - If `isStreaming` and `playlistUrl`: Render HLSPlayer
   - Else: Use existing expo-av Audio.Sound flow

3. Integrate HLSPlayer component:
   - Pass playlist URL to HLSPlayer
   - Handle playback events (start, complete, error)
   - Update UI state based on HLS player state

4. Update play/pause toggle:
   - If streaming: Control HLSPlayer
   - If not streaming: Control Audio.Sound (existing)

5. Add streaming status indicators:
   - Show "Streaming..." during live playlist
   - Show "Complete" when stream finished
   - Show segment progress if available (X/Y segments)

6. Handle the transition:
   - Streaming starts: Begin HLS playback
   - Stream completes: Update UI, enable download
   - User can replay from HLS playlist after completion

7. Error handling:
   - HLS errors: Show message, offer retry
   - Network errors: HLS.js handles retry automatically
   - Fatal errors: Fall back to "generation failed" state

**Verification Checklist**:
- [x] HLSPlayer renders when streaming
- [x] Audio.Sound used when not streaming
- [x] Play/pause controls work for both modes
- [x] Streaming status displayed
- [x] Error states handled
- [x] Transition from streaming to complete works

**Testing Instructions**:

Unit tests to write:
- Test HLSPlayer rendered when isStreaming=true
- Test Audio.Sound used when isStreaming=false
- Test play/pause controls for streaming mode
- Test error state rendering

Mocking required:
- Mock HLSPlayer component
- Mock expo-av Audio
- Mock playback state

Run tests:
```bash
npm test -- --testPathPattern="MeditationControls"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): integrate HLS streaming into MeditationControls

Add conditional rendering for streaming vs base64 playback
Integrate HLSPlayer component for streaming mode
Update play/pause controls for both modes
```

---

### Task 6: Add Download Button Component

**Goal**: Create a download button that triggers MP3 generation and saves the file locally.

**Files to Modify/Create**:
- `frontend/components/DownloadButton.tsx` - New download button component
- `tests/frontend/unit/DownloadButton-test.tsx` - Unit tests

**Prerequisites**:
- Task 4 complete (API client has getDownloadUrl)

**Implementation Steps**:

1. Define component interface:
   ```typescript
   interface DownloadButtonProps {
     jobId: string;
     userId: string;
     disabled?: boolean;
     onDownloadStart?: () => void;
     onDownloadComplete?: (filePath: string) => void;
     onDownloadError?: (error: Error) => void;
   }
   ```

2. Implement download flow:
   - On press: Show loading state
   - Call API to get download URL
   - Download file from URL
   - Save to appropriate location based on platform

3. Platform-specific file handling:
   - **Web**: Create blob URL, trigger download via anchor click
   - **Mobile**: Use expo-file-system to download to documents directory
   - Use platform detection for correct implementation

4. Web download implementation:
   - Fetch MP3 from download URL
   - Create Blob from response
   - Create object URL
   - Create hidden anchor element with download attribute
   - Programmatically click to trigger download
   - Revoke object URL after download

5. Mobile download implementation:
   - Use `FileSystem.downloadAsync` from expo-file-system
   - Save to `FileSystem.documentDirectory`
   - Generate filename: `meditation_{timestamp}.mp3`
   - Optionally trigger share sheet for user to choose location

6. UI states:
   - Default: Download icon + "Download MP3"
   - Loading: Spinner + "Preparing..."
   - Success: Checkmark + "Downloaded"
   - Error: Error icon + "Retry"

7. Error handling:
   - Network errors during download
   - API errors (MP3 not ready, generation failed)
   - Storage errors (disk full, permissions)

**Verification Checklist**:
- [x] Button triggers download flow
- [x] Loading state shown during download
- [x] Web download works (file saves)
- [x] Mobile download works (file saves)
- [x] Success state shown after download
- [x] Error state shown on failure
- [x] Retry works after error

**Testing Instructions**:

Unit tests to write:
- Test button renders with correct initial state
- Test loading state during download
- Test success state after download
- Test error state on failure
- Test retry functionality

Mocking required:
- Mock fetch for download URL API
- Mock FileSystem for mobile
- Mock Blob/URL for web

Run tests:
```bash
npm test -- --testPathPattern="DownloadButton"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): add DownloadButton component for MP3 download

Implement platform-specific download handling
Add loading, success, and error states
Support retry on failure
```

---

### Task 7: Integrate Download Button into Meditation Flow

**Goal**: Add the download button to the meditation completion screen.

**Files to Modify/Create**:
- `frontend/components/ScreenComponents/MeditationControls.tsx` - Add download button
- Screen component that contains MeditationControls (identify and modify)

**Prerequisites**:
- Task 5 complete (MeditationControls updated for streaming)
- Task 6 complete (DownloadButton ready)

**Implementation Steps**:

1. Identify where download button should appear:
   - After streaming completes
   - Below or beside playback controls
   - Should not appear during streaming (only after)

2. Add conditional rendering:
   - Show download button when:
     - `isStreaming` is true AND
     - Stream is complete (all segments received) AND
     - Download not already completed
   - Hide/disable when:
     - Still streaming (segments loading)
     - Download already completed
     - In base64 mode (already have full audio)

3. Wire up download callbacks:
   - Pass jobId and userId to DownloadButton
   - Handle download complete: Update UI state
   - Handle download error: Show error toast/message

4. Update meditation result tracking:
   - Track whether download was completed
   - Store downloaded file path for future reference
   - Consider persisting to AsyncStorage for meditation history

5. UI layout considerations:
   - Download button should be visually secondary to playback controls
   - Show alongside replay controls
   - Consider "Save to Library" wording for clarity

**Verification Checklist**:
- [x] Download button appears after streaming completes
- [x] Download button hidden during streaming
- [x] Download button hidden in base64 mode
- [x] Download callbacks work correctly
- [x] UI updates after successful download

**Testing Instructions**:

Unit tests to write:
- Test download button appears when streaming complete
- Test download button hidden during streaming
- Test download button hidden in base64 mode
- Test callback integration

Mocking required:
- Mock DownloadButton component
- Mock streaming state

Run tests:
```bash
npm test -- --testPathPattern="MeditationControls"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): integrate download button into meditation flow

Add download button after streaming completes
Hide during active streaming and base64 mode
Wire up download callbacks
```

---

### Task 8: Add Error Handling and Retry UI

**Goal**: Implement comprehensive error handling with user-friendly retry options.

**Files to Create**:
- `frontend/components/ErrorBoundary.tsx` - Error boundary for HLS errors (does not exist)
- `frontend/components/StreamingError.tsx` - Error display component
- `tests/frontend/unit/StreamingError-test.tsx` - Unit tests

**Files to Modify**:
- `frontend/components/ScreenComponents/MeditationControls.tsx` - Error state handling

**Prerequisites**:
- Tasks 5-7 complete

**Implementation Steps**:

1. Create StreamingError component:
   ```typescript
   interface StreamingErrorProps {
     error: Error;
     onRetry: () => void;
     canRetry: boolean;
   }
   ```
   - Display user-friendly error message
   - Show retry button if canRetry is true
   - Map error types to user messages

2. Error message mapping:
   - Network error: "Connection lost. Check your internet and try again."
   - HLS fatal error: "Playback failed. Tap retry to start over."
   - Generation failed: "Could not generate meditation. Please try again."
   - Download failed: "Download failed. Tap to retry."

3. Update MeditationControls error handling:
   - Catch errors from HLSPlayer
   - Catch errors from API client
   - Display StreamingError component
   - Wire up retry callback

4. Implement retry logic:
   - HLS playback error: Reinitialize player with same URL
   - Generation error: Re-submit meditation request
   - Download error: Retry download

5. Add error boundary for unexpected errors:
   - Wrap HLS components in error boundary
   - Log errors for debugging
   - Show generic error UI with retry

6. Timeout handling:
   - If no segments received in 30 seconds: Show timeout error
   - If stream stalls for 15 seconds: Offer retry option

**Verification Checklist**:
- [x] StreamingError component renders correctly
- [x] Error messages are user-friendly
- [x] Retry button triggers correct action
- [x] Error boundary catches unexpected errors
- [x] Timeout errors handled

**Testing Instructions**:

Unit tests to write:
- Test StreamingError renders error message
- Test retry button calls callback
- Test error type to message mapping
- Test error boundary fallback render

Mocking required:
- Mock error objects
- Mock retry callbacks

Run tests:
```bash
npm test -- --testPathPattern="StreamingError"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): add error handling and retry UI for streaming

Create StreamingError component with retry support
Add user-friendly error message mapping
Implement error boundary for HLS components
Handle timeout scenarios
```

---

### Task 9: Update Loading States for Streaming

**Goal**: Improve loading UI to reflect the faster time-to-audio with streaming.

**Files to Create**:
- `frontend/components/ScreenComponents/MeditationLoading.tsx` - New loading component for streaming states (no existing dedicated loading component - loading UI is currently inline in MeditationControls)

**Files to Modify**:
- `frontend/components/ScreenComponents/MeditationControls.tsx` - Update loading integration to use new component

**Prerequisites**:
- Tasks 1-8 complete

**Implementation Steps**:

1. Identify current loading UI:
   - Find existing loading indicator during meditation generation
   - Understand current messaging ("Generating meditation...")

2. Update loading states for streaming:
   - "Starting meditation..." (initial request)
   - "Preparing audio..." (job created, waiting for first segment)
   - "Ready to play" (first segment available, playback starting)
   - Remove/shorten the long wait message

3. Add progress indicator:
   - If segments_total known: Show X/Y segments
   - If unknown: Show indeterminate progress
   - Update as segments arrive

4. Optimize perceived wait time:
   - Show playback controls as soon as playlist URL available
   - Begin playback attempt immediately (HLS.js will buffer)
   - Loading spinner on play button until audio actually starts

5. Consider animation:
   - Smooth transition from loading to playback
   - Avoid jarring UI changes

**Verification Checklist**:
- [x] Loading messages updated for streaming
- [x] Progress shown when available
- [x] Fast transition to playback UI
- [x] No jarring UI changes

**Testing Instructions**:

Unit tests to write:
- Test loading state messages
- Test progress display
- Test transition to playback UI

Mocking required:
- Mock job status with different states

Run tests:
```bash
npm test -- --testPathPattern="MeditationLoading"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(frontend): update loading states for streaming playback

Improve loading messages for faster perceived startup
Add segment progress indicator
Optimize transition to playback UI
```

---

### Task 10: Integration Test Suite for Frontend HLS

**Goal**: Create end-to-end tests for the complete streaming flow in the frontend.

**Files to Modify/Create**:
- `tests/frontend/integration/hls-streaming-test.tsx` - Integration tests
- `tests/frontend/integration/test-utils.tsx` - Test utilities (update if needed)

**Prerequisites**:
- Tasks 1-9 complete

**Implementation Steps**:

1. Set up test environment:
   - Mock fetch for all API calls
   - Mock HLS.js with controllable events
   - Mock WebView for mobile tests
   - Mock FileSystem for download tests

2. Test: Complete streaming flow
   - Render meditation screen
   - Trigger meditation request
   - Mock API returns streaming job
   - Verify HLSPlayer rendered with playlist URL
   - Trigger playback events
   - Verify UI updates correctly
   - Trigger completion
   - Verify download button appears

3. Test: Download flow
   - Start from completed streaming state
   - Click download button
   - Mock download URL response
   - Mock file download
   - Verify success state

4. Test: Error recovery
   - Simulate HLS error during playback
   - Verify error UI shown
   - Click retry
   - Verify playback reinitializes

5. Test: Fallback to base64
   - Mock API returns non-streaming job
   - Verify expo-av Audio used instead of HLSPlayer
   - Verify existing flow works unchanged

6. Platform-specific tests:
   - Test web-specific code paths
   - Test mobile-specific code paths (WebView)

**Verification Checklist**:
- [x] All integration tests pass
- [x] Tests cover happy path
- [x] Tests cover error scenarios
- [x] Tests cover fallback behavior
- [x] Tests work in CI (no network calls)

**Testing Instructions**:

Run integration tests:
```bash
npm test -- --testPathPattern="hls-streaming"
```

Ensure tests work in CI:
- All fetch calls mocked
- All native modules mocked

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

test(frontend): add integration tests for HLS streaming flow

Test complete streaming playback flow
Test download functionality
Test error recovery
Test base64 fallback
```

---

## Phase Verification

### Complete Test Suite
Run all frontend tests:
```bash
npm test
```

All tests must pass.

### Manual Verification Steps
After deployment with Phase 1 backend:

**Web testing:**
1. Open app in Chrome/Firefox/Safari
2. Start meditation generation
3. Verify playback begins within ~5 seconds
4. Verify audio plays smoothly
5. Wait for completion, verify download button appears
6. Click download, verify MP3 saves
7. Test error recovery (disconnect network mid-stream)

**iOS testing:**
1. Run app in iOS Simulator or device
2. Repeat steps 2-7 from web testing
3. Verify WebView player works correctly
4. Note: No background playback expected

**Android testing:**
1. Run app in Android Emulator or device
2. Repeat steps 2-7 from web testing
3. Verify WebView player works correctly
4. Note: No background playback expected

### Integration Points Verified
- Frontend receives streaming job status correctly
- Playlist URL works and returns valid HLS content
- HLS.js/WebView plays streaming audio
- Download endpoint returns valid MP3 URL
- Downloaded MP3 plays correctly

### Known Limitations
- No background playback on mobile (WebView limitation)
- No lock screen controls on mobile
- Foreground-only playback during meditation

### Technical Debt
- Consider native player migration for background playback
- Consider lock screen control integration
- Consider offline caching of completed meditations

