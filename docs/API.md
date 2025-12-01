# Float API Documentation

This document describes the AWS Lambda API endpoints for Float meditation app.

## Base URL

```
https://<your-lambda-function-url>/
```

Set `EXPO_PUBLIC_LAMBDA_FUNCTION_URL` in frontend `.env` with your Lambda URL.

## Authentication

Currently, the API does not require authentication. Future versions may add API key or JWT validation.

## Request Format

All requests must be POST with `Content-Type: application/json`.

**Common Headers**:

```
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
- Text input maximum 5000 characters

**Response (200 OK)**:

```json
{
  "statusCode": 200,
  "body": {
    "request_id": "req_abc123def456",
    "user_id": "user@example.com",
    "sentiment": "anxious",
    "intensity": 0.78,
    "reasoning": "User expressed worry about upcoming presentation and stress about deadline.",
    "timestamp": "2024-10-31T12:34:56Z"
  }
}
```

**Response Fields**:

| Field        | Type   | Description                                               |
| ------------ | ------ | --------------------------------------------------------- |
| `request_id` | string | Unique request identifier for tracking                    |
| `user_id`    | string | Echo of user ID                                           |
| `sentiment`  | string | Detected emotion (anxious, sad, happy, angry, calm, etc.) |
| `intensity`  | number | Emotion intensity from 0.0 (weak) to 1.0 (strong)         |
| `reasoning`  | string | AI explanation of why this emotion was detected           |
| `timestamp`  | string | ISO 8601 timestamp of analysis                            |

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
    "error": "Invalid inference_type",
    "details": "inference_type must be 'summary' or 'meditation'"
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
    "created_at": "2024-10-31T12:34:56Z",
    "updated_at": "2024-10-31T12:35:00Z"
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
    "result": {
      "request_id": "req_xyz789abc123",
      "user_id": "user@example.com",
      "base64": "SUQzBAAAAAAAI1...(long base64 string)...==",
      "music_list": ["rain.mp3", "forest.mp3"]
    }
  }
}
```

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

  // Step 2: Poll for completion
  while (true) {
    const statusResponse = await fetch(
      `${LAMBDA_URL}/job/${job_id}?user_id=${userId}`
    );
    const job = await statusResponse.json();

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

### Example 3: Generate Meditation (JavaScript)

```javascript
async function generateMeditation(userId, floats, musicList) {
  const response = await fetch(process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      inference_type: 'meditation',
      input_data: { floats },
      music_list: musicList,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.body?.details || 'Generation failed');
  }

  return response.json();
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

// Decode and play audio
const audioData = result.body.base64_audio;
const blob = new Blob([Uint8Array.from(atob(audioData), (c) => c.charCodeAt(0))], {
  type: 'audio/mp3',
});
const audioUrl = URL.createObjectURL(blob);
audioElement.src = audioUrl;
audioElement.play();
```

## CORS

The API includes CORS headers to allow requests from web clients:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
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
- **Logs**: CloudWatch logs retained for 7 days

## Future Enhancements

- [ ] API versioning (v1, v2)
- [ ] Batch meditation generation
- [ ] Custom voice selection
- [ ] Duration preference parameter
- [ ] Background music selection UI
- [ ] Meditation history retrieval
- [ ] User preferences/settings

