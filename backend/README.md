# Float Backend

This is the backend service for the Float meditation app, built as an AWS Lambda function that handles meditation generation, sentiment analysis, and audio processing.

## Architecture

The backend is structured as a serverless AWS Lambda function with a clean, modular architecture:

```
backend/
├── lambda_function.py          # Lambda entry point
├── requirements.txt           # Python dependencies
└── src/
    ├── config/               # Configuration and constants
    ├── handlers/             # Request handlers and middleware
    ├── models/               # Data models and schemas
    ├── providers/           # External service providers (TTS)
    ├── services/            # Business logic services
    └── utils/               # Utility functions
```

## Features

- **Sentiment Analysis**: Processes user input (text/audio) to determine emotion and intensity using Google Gemini AI
- **Meditation Generation**: Creates personalized meditation content based on user sentiment data
- **Multi-Provider TTS**: Supports multiple text-to-speech providers:
  - Google Cloud Text-to-Speech
  - OpenAI TTS
  - ElevenLabs TTS
- **Audio Processing**: Uses FFmpeg for audio manipulation and enhancement
- **Cloud Storage**: Stores generated content and user data in AWS S3
- **CORS Support**: Handles cross-origin requests for web clients
- **Request Validation**: Comprehensive middleware for request validation and error handling

## API Endpoints

The Lambda function handles two main inference types:

### Summary Request
Analyzes user input and generates sentiment summary.

**Request Format:**
```json
{
  "inference_type": "summary",
  "user_id": "string",
  "audio": "base64_encoded_audio | NotAvailable",
  "prompt": "text_input | NotAvailable"
}
```

**Response Format:**
```json
{
  "request_id": 12345,
  "user_id": "string",
  "inference_type": "summary",
  "sentiment_label": "Happy|Sad|Angry|...",
  "intensity": "1-5",
  "speech_to_text": "transcribed_text",
  "added_text": "user_provided_text",
  "summary": "ai_generated_summary",
  "user_summary": "personalized_summary",
  "user_short_summary": "brief_summary"
}
```

### Meditation Request
Generates personalized meditation audio based on input data.

**Request Format:**
```json
{
  "inference_type": "meditation",
  "user_id": "string",
  "input_data": "summary_data_or_list",
  "music_list": ["background_track1.wav", "background_track2.wav"]
}
```

**Response Format:**
```json
{
  "request_id": 12345,
  "user_id": "string",
  "inference_type": "meditation",
  "music_list": ["updated_music_list"],
  "base64": "base64_encoded_meditation_audio"
}
```

## Environment Variables

Configure the following environment variables in your Lambda function:

```bash
# Google AI
G_KEY=<google_gemini_api_key>

# Text-to-Speech Providers
XI_KEY=<eleven_labs_api_key>
OPENAI_API_KEY=<openai_api_key>

# TTS Configuration
SIMILARITY_BOOST=0.7
STABILITY=0.3
STYLE=0.3
VOICE_ID=jKX50Q2OBT1CsDwwcTkZ

# Audio Processing
FFMPEG_BINARY=/opt/bin/ffmpeg

# AWS Configuration (automatically provided by Lambda)
AWS_ACCESS_KEY_ID=<auto_provided>
AWS_SECRET_ACCESS_KEY=<auto_provided>
AWS_DEFAULT_REGION=<auto_provided>
```

## Dependencies

Key Python packages (see `requirements.txt`):

- `google-generativeai` - Google Gemini AI integration
- `boto3` - AWS SDK for S3 storage
- `requests` - HTTP client for external APIs
- `pydub` - Audio processing utilities

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate permissions
2. Lambda layer with FFmpeg binary
3. Python 3.12 runtime environment

### Build and Deploy

1. **Install dependencies on Linux (required for Lambda compatibility):**
   ```bash
   pip install -r requirements.txt -t .
   ```

2. **Create deployment package:**
   ```bash
   zip -r lambda-deployment.zip .
   ```

3. **Deploy to AWS Lambda:**
   - Upload the zip file to your Lambda function
   - Set runtime to Python 3.12
   - Configure environment variables
   - Add FFmpeg layer

### FFmpeg Layer

The backend requires an FFmpeg layer for audio processing. Create a Lambda layer containing the FFmpeg binary at `/opt/bin/ffmpeg`. 

Refer to [this guide](https://virkud-sarvesh.medium.com/building-ffmpeg-layer-for-a-lambda-function-a206f36d3edc) for creating the FFmpeg layer.

## Local Development

For local testing, you can simulate Lambda events:

```python
from src.handlers.lambda_handler import lambda_handler

# Test event
event = {
    "inference_type": "summary",
    "user_id": "test_user",
    "prompt": "I feel happy today"
}

context = {}  # Mock Lambda context

response = lambda_handler(event, context)
print(response)
```

## Middleware Chain

The request processing follows this middleware chain:

1. **CORS Middleware** - Handles preflight requests and adds CORS headers
2. **JSON Middleware** - Parses request body (supports both API Gateway and direct invocation)
3. **Method Validation** - Validates HTTP methods (skipped for direct invocation)
4. **Request Validation** - Validates required fields and data types
5. **Error Handling** - Catches and formats errors

## Error Handling

The backend provides comprehensive error handling with structured responses:

```json
{
  "statusCode": 400|500,
  "headers": {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
  },
  "body": "{\"error\": \"Error message\", \"details\": \"Optional details\"}"
}
```

## Performance Considerations

- **Cold Start Optimization**: Dependencies are loaded efficiently to minimize cold start times
- **Memory Configuration**: Recommended 4GB memory for audio processing tasks
- **Timeout**: Configure 15-minute timeout for complex meditation generation
- **Concurrent Execution**: Design supports concurrent requests with isolated processing

## Monitoring and Logging

The backend includes comprehensive logging for debugging and monitoring:

- Request/response logging
- Middleware execution tracking
- Error tracking with stack traces
- Performance metrics logging

Monitor your Lambda function through AWS CloudWatch for:
- Execution duration
- Memory usage
- Error rates
- Invocation counts

## Security

- **Input Validation**: All inputs are validated and sanitized
- **Error Sanitization**: Sensitive information is not exposed in error responses
- **CORS Configuration**: Properly configured for cross-origin requests
- **Environment Variables**: Sensitive data stored as encrypted environment variables

## Contributing

When contributing to the backend:

1. Follow the existing modular architecture
2. Add comprehensive logging for debugging
3. Include proper error handling
4. Update type hints and documentation
5. Test with both API Gateway and direct Lambda invocation formats

## License

This project is licensed under the Apache 2.0 License. See the LICENSE file for details.