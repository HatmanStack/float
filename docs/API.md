# Float API Documentation

This document describes the AWS Lambda API endpoints for Float meditation app.

## Base URL

```text
https://<your-lambda-function-url>/
```

Set `EXPO_PUBLIC_LAMBDA_FUNCTION_URL` in frontend `.env` with your Lambda URL.

## Authentication

Float uses a privacy-first authorization model rather than server-issued
credentials:

- The `user_id` is generated client-side (guest users get a stable
  anonymous UUID; signed-in users use their Google `sub`).
- Every endpoint that touches user-scoped state requires `user_id` on the
  request body or query string and validates it against the path's
  `job_id` via `_authorize_job_access`. A mismatch returns **403
  Forbidden**.
- `user_id` is format-validated at the request boundary (see
  `backend/src/utils/validation.py::is_valid_user_id`). Path-traversal
  patterns such as `..`, `/`, and empty strings are rejected with **400**.
- Guest mode is supported — there is no sign-in requirement.

A future auth plan may add server-minted opaque user identifiers and
JWTs; the broader identity overhaul is out of scope for the 2026-04-08
audit remediation.

## Request Format

Requests use POST for submissions and GET for job status polling. All POST requests require `Content-Type: application/json`.

**Common Headers**:

```text
Content-Type: application/json
```

**Error Responses**:

```json
{
  "statusCode": 400,
  "body": {
    "error": "Error type",
    "details": "Detailed error message"
  }
}
```

## Endpoints

### 1. Summary Inference

Analyze emotion from audio and/or text input.

**Endpoint**: `POST /`

**Request Body**:

```json
{
  "user_id": "user@example.com",
  "inference_type": "summary",
  "audio": "base64_encoded_audio_or_NotAvailable",
  "prompt": "user text or NotAvailable"
}
```

**Request Fields**:

| Field            | Type   | Required | Description                                   |
| ---------------- | ------ | -------- | --------------------------------------------- |
| `user_id`        | string | Yes      | Unique user identifier                        |
| `inference_type` | string | Yes      | Must be `"summary"`                           |
| `audio`          | string | No       | Base64 encoded audio file or `"NotAvailable"` |
| `prompt`         | string | No       | User text input or `"NotAvailable"`           |

**Constraints**:

- At least one of `audio` or `prompt` must be provided and not "NotAvailable"
- Audio should be base64 encoded MP3/WAV
- Text input maximum 10000 characters

**Response (200 OK)**:

```json
{
  "statusCode": 200,
  "body": {
    "request_id": 12345,
    "user_id": "user@example.com",
    "inference_type": "summary",
    "sentiment_label": "Fearful",
    "intensity": "high",
    "speech_to_text": "I'm worried about my presentation tomorrow",
    "added_text": "NotAvailable",
    "summary": "User is experiencing anxiety about an upcoming presentation.",
    "user_summary": "You're feeling fearful about your presentation. This is a common stress response.",
    "user_short_summary": "Presentation anxiety"
  }
}
```

**Response Fields**:

| Field | Type | Description |
|---|---|---|
| `request_id` | number | Unique request identifier for tracking |
| `user_id` | string | Echo of user ID |
| `inference_type` | string | Always `"summary"` |
| `sentiment_label` | string | Detected emotion (Angry, Disgusted, Fearful, Happy, Neutral, Sad, Surprised) |
| `intensity` | string | Summary-inference intensity label: `"high"`, `"medium"`, or `"low"`. Note: the meditation endpoint instead accepts a numeric `intensity` on each float (e.g., `0.8`) — see "Meditation Generation" below. |
| `speech_to_text` | string | Transcription of audio input, or `"NotAvailable"` |
| `added_text` | string | Additional text context, or `"NotAvailable"` |
| `summary` | string | AI-generated summary of the emotional state |
| `user_summary` | string | User-facing explanation of detected emotion |
| `user_short_summary` | string | Brief label for the float |

**Error Examples**:

Missing both audio and prompt:

```json
{
  "statusCode": 400,
  "body": {
    "error": "Validation error",
    "details": "At least one of audio or prompt must be provided"
  }
}
```

Invalid request type:

```json
{
  "statusCode": 400,
  "body": {
    "error": "Validation error",
    "details": "Invalid inference_type: foo"
  }
}
```

### 2. Meditation Generation (Async)

Generate a personalized meditation from selected floats (emotions/incidents). Uses async processing pattern due to long generation times (1-2 minutes).

**Step 1: Submit Request**

**Endpoint**: `POST /`

**Request Body**:

```json
{
  "user_id": "user@example.com",
  "inference_type": "meditation",
  "input_data": {
    "floats": [
      {
        "sentiment": "anxious",
        "intensity": 0.8,
        "description": "Worried about presentation"
      },
      {
        "sentiment": "sad",
        "intensity": 0.6,
        "description": "Missing a friend"
      }
    ]
  },
  "music_list": ["rain.mp3", "forest.mp3"]
}
```

**Request Fields**:

| Field            | Type            | Required | Description                         |
| ---------------- | --------------- | -------- | ----------------------------------- |
| `user_id`        | string          | Yes      | Unique user identifier              |
| `inference_type` | string          | Yes      | Must be `"meditation"`              |
| `input_data`     | object or array | Yes      | Float data (dict or list of dicts)  |
| `music_list`     | array           | Yes      | List of background music file names |
| `duration_minutes` | number | No | Meditation length: 3, 5, 10, 15, or 20 (default: 5) |
| `qa_transcript` | array | No | Q&A turns captured from the onboarding voice flow. Each item is `{ role: "user" \| "assistant", text: string }` (see `QATranscriptItem` in `backend/src/models/requests.py`). Used by the meditation prompt as additional context. |

**Constraints**:

- `input_data` must not be empty
- `music_list` must not be empty
- Maximum 3 floats recommended
- Meditation generation takes 1-2 minutes

**Response (200 OK)** - Job Created:

```json
{
  "statusCode": 200,
  "body": {
    "job_id": "6723b3ea-a86f-4364-846e-69598adb82aa",
    "status": "pending",
    "message": "Meditation generation started. Poll /job/{job_id} for status."
  }
}
```

When HLS streaming is enabled (default), the response also includes:

```json
{
  "streaming": {
    "enabled": true,
    "playlist_url": null
  }
}
```

The `playlist_url` becomes available once streaming processing begins. Poll `/job/{job_id}` to get the updated URL.

**Step 2: Poll for Status**

**Endpoint**: `GET /job/{job_id}?user_id={user_id}`

**Response (Job Pending/Processing)**:

```json
{
  "statusCode": 200,
  "body": {
    "job_id": "6723b3ea-a86f-4364-846e-69598adb82aa",
    "user_id": "user@example.com",
    "status": "processing",
    "created_at": "2026-04-08T12:34:56Z",
    "updated_at": "2026-04-08T12:35:00Z",
    "generation_attempt": 1,
    "streaming": {
      "enabled": true,
      "started_at": "2026-04-08T12:35:02Z",
      "playlist_url": "https://.../user/<id>/job/<id>/playlist.m3u8?X-Amz-..."
    },
    "download": {
      "available": false
    }
  }
}
```

**Response (Job Completed)**:

```json
{
  "statusCode": 200,
  "body": {
    "job_id": "6723b3ea-a86f-4364-846e-69598adb82aa",
    "user_id": "user@example.com",
    "status": "completed",
    "created_at": "2026-04-08T12:34:56Z",
    "updated_at": "2026-04-08T12:36:10Z",
    "generation_attempt": 1,
    "streaming": {
      "enabled": true,
      "started_at": "2026-04-08T12:35:02Z",
      "playlist_url": "https://.../user/<id>/job/<id>/playlist.m3u8?X-Amz-..."
    },
    "download": {
      "available": true
    },
    "result": {
      "request_id": "req_xyz789abc123",
      "user_id": "user@example.com",
      "base64": "SUQzBAAAAAAAI1...(long base64 string)...==",
      "music_list": ["rain.mp3", "forest.mp3"]
    }
  }
}
```

Fields:

| Field | Type | Description |
|---|---|---|
| `status` | string | `pending` \| `processing` \| `completed` \| `failed` |
| `generation_attempt` | number | 1-based attempt counter, capped at `MAX_GENERATION_ATTEMPTS` (3) |
| `streaming.enabled` | boolean | Whether HLS streaming is active for this job |
| `streaming.playlist_url` | string \| null | Pre-signed HLS playlist URL; `null` until the streaming watcher has written the first segment |
| `download.available` | boolean | `true` once the MP3 has been fully encoded and the `/job/{job_id}/download` endpoint will succeed |
| `result.base64` | string | Full MP3 bytes, base64-encoded, only present on `status: completed` |

**Response (Job Failed)**:

```json
{
  "statusCode": 200,
  "body": {
    "job_id": "6723b3ea-a86f-4364-846e-69598adb82aa",
    "status": "failed",
    "error": "Failed to generate speech audio"
  }
}
```

**Job Status Values**:

| Status       | Description                           |
| ------------ | ------------------------------------- |
| `pending`    | Job created, not yet started          |
| `processing` | AI/TTS generation in progress         |
| `completed`  | Audio ready in `result.base64`        |
| `failed`     | Generation failed, see `error` field  |

**Client Usage**:

```typescript
async function generateMeditation(userId, floats, musicList) {
  // Step 1: Submit job
  const submitResponse = await fetch(LAMBDA_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      inference_type: 'meditation',
      input_data: { floats },
      music_list: musicList,
    }),
  });
  const { job_id } = await submitResponse.json();

  // Step 2: Poll for completion; start playback as soon as the HLS
  // playlist URL is available, even before status === 'completed'.
  let startedStreaming = false;
  while (true) {
    const statusResponse = await fetch(
      `${LAMBDA_URL}/job/${job_id}?user_id=${userId}`
    );
    const job = await statusResponse.json();

    // Start streaming as soon as the playlist URL is published.
    const playlistUrl = job.streaming?.playlist_url;
    if (!startedStreaming && playlistUrl) {
      startedStreaming = true;
      onStream(playlistUrl); // hand off to your HLS player
    }

    if (job.status === 'completed') {
      return job.result;
    }
    if (job.status === 'failed') {
      throw new Error(job.error);
    }

    await new Promise(resolve => setTimeout(resolve, 3000)); // Poll every 3s
  }
}
```

**Error Examples**:

Invalid meditation data:

```json
{
  "statusCode": 400,
  "body": {
    "error": "Validation error",
    "details": "input_data is required and must not be empty"
  }
}
```

Job not found:

```json
{
  "statusCode": 404,
  "body": {
    "error": "Job 6723b3ea-a86f-4364-846e-69598adb82aa not found"
  }
}
```

### 3. Download Meditation

Request a pre-signed download URL for the MP3 of a completed meditation.
The endpoint does **not** stream audio bytes; it returns JSON with a
short-lived S3 pre-signed URL that the client should fetch directly.

**Endpoint**: `POST /job/{job_id}/download?user_id=user@example.com`

The `user_id` is passed as a query parameter. No request body is required.
The job must already be in `status: completed` and have
`download.available === true` (see the job-status response above).

**Response (200 OK)**:

```json
{
  "statusCode": 200,
  "body": {
    "job_id": "6723b3ea-a86f-4364-846e-69598adb82aa",
    "download_url": "https://<bucket>.s3.amazonaws.com/user/<id>/meditation.mp3?X-Amz-...",
    "expires_in": 3600
  }
}
```

`expires_in` is seconds. The client should fetch `download_url` directly
(GET, no auth headers); the pre-signed URL embeds the S3 credentials.

**Error Responses**:

- **400** — invalid `user_id` format
- **403** — `user_id` does not own `job_id`
- **404** — job not found
- **409** — job not yet completed, or the MP3 is not available

### 4. Gemini Live Token

Issue an opaque, short-lived marker that the Gemini Live WebSocket hook
presents when establishing a voice session. As of Phase 2 Task 1 of the
2026-04-08 audit remediation, this endpoint **no longer** returns the
raw `GEMINI_API_KEY`; it returns an HMAC-derived opaque marker with a
60-second TTL (`TOKEN_MARKER_TTL_SECONDS`).

**Endpoint**: `POST /token?user_id=<user_id>`

**Response (200 OK)**:

```json
{
  "statusCode": 200,
  "body": {
    "token": "<opaque HMAC marker>",
    "expires_in": 60,
    "user_id": "user@example.com",
    "endpoint": "wss://generativelanguage.googleapis.com/ws/..."
  }
}
```

**Notes**:

- The marker is cryptographically bound to `user_id` and the server's
  `GEMINI_API_KEY`; clients must treat it as opaque and must not attempt
  to use it with the raw Gemini REST API.
- The legacy behaviour (returning the raw API key as the token) is
  considered a security bug and is removed.

## Common Error Codes

| Code | Error                  | Meaning                     | Solution                      |
| ---- | ---------------------- | --------------------------- | ----------------------------- |
| 400  | Bad Request            | Invalid input data          | Check request format          |
| 400  | Validation Error       | Missing required fields     | Add all required fields       |
| 400  | Invalid inference_type | Unknown type                | Use "summary" or "meditation" |
| 500  | Server Error           | Backend processing failed   | Retry, check logs             |
| 500  | AI Service Error       | Google Gemini API failed    | Retry, check API quota        |
| 500  | TTS Error              | OpenAI TTS failed           | Retry, check API key          |
| 500  | Timeout                | Processing took >15 minutes | Try simpler input             |

## Usage Examples

### Example 1: Analyze a Float (Audio)

```bash
curl -X POST https://your-lambda-url/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "inference_type": "summary",
    "audio": "SUQzBAA...",
    "prompt": "NotAvailable"
  }'
```

### Example 2: Analyze a Float (Text)

```bash
curl -X POST https://your-lambda-url/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "inference_type": "summary",
    "audio": "NotAvailable",
    "prompt": "I am feeling very stressed about my job interview next week"
  }'
```

### Example 3: Generate Meditation (JavaScript, async + polling)

Meditation generation is asynchronous. `POST /` returns a `job_id`
immediately; the client must poll `GET /job/{job_id}` until
`status === "completed"` before reading `result.base64`.

```javascript
const LAMBDA_URL = process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL;

async function generateMeditation(userId, floats, musicList) {
  // Step 1: submit the job
  const submit = await fetch(LAMBDA_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      inference_type: 'meditation',
      input_data: { floats },
      music_list: musicList,
    }),
  });
  if (!submit.ok) {
    const err = await submit.json();
    throw new Error(err.body?.details || 'Generation failed');
  }
  const { job_id } = (await submit.json()).body;

  // Step 2: poll until completed or failed
  while (true) {
    const res = await fetch(
      `${LAMBDA_URL}/job/${job_id}?user_id=${encodeURIComponent(userId)}`
    );
    const job = (await res.json()).body;

    if (job.status === 'completed') {
      return job.result; // { base64, music_list, ... }
    }
    if (job.status === 'failed') {
      throw new Error(job.error || 'Meditation generation failed');
    }
    await new Promise((r) => setTimeout(r, 3000));
  }
}

// Usage
const result = await generateMeditation(
  'user@example.com',
  [
    { sentiment: 'anxious', intensity: 0.8, description: 'Work stress' },
    { sentiment: 'sad', intensity: 0.5, description: 'Missing home' },
  ],
  ['rain.mp3', 'forest.mp3']
);

// Decode and play audio once the job is complete.
const blob = new Blob(
  [Uint8Array.from(atob(result.base64), (c) => c.charCodeAt(0))],
  { type: 'audio/mp3' }
);
const audioUrl = URL.createObjectURL(blob);
audioElement.src = audioUrl;
audioElement.play();
```

## CORS

The API includes CORS headers to allow requests from web clients:

```text
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: OPTIONS, POST, GET
Access-Control-Allow-Headers: Content-Type
```

## Rate Limiting

Currently no rate limiting. Future versions may add:

- Per-user limits (e.g., 5 meditations/hour)
- Concurrent request limits
- Token-based throttling

## Performance Characteristics

### Summary Request

- **Time**: 5-15 seconds
- **Cost**: ~$0.001 (API calls)

### Meditation Request

- **Time**: 30-90 seconds (includes TTS synthesis)
- **Cost**: ~$0.01-0.05 (AI + TTS)

## Data Retention

- **User Floats**: Stored in S3 indefinitely
- **Meditation Requests**: Stored in S3 for 30 days
- **Logs**: CloudWatch logs retained for 14 days

## Future Enhancements

- [ ] API versioning (v1, v2)
- [ ] Batch meditation generation
- [ ] Custom voice selection
- [ ] Background music selection UI
- [ ] Meditation history retrieval
- [ ] User preferences/settings
