import sys
import os
import json
import logging
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_local_execution():
    """
    Verifies Lambda execution by mocking AWS services and environment variables.
    """
    print("=========================================")
    print("Verifying Lambda Function Locally (Mocked)")
    print("=========================================")

    # Mock environment variables
    env_vars = {
        "ENVIRONMENT": "staging",
        "AWS_S3_BUCKET": "mock-cust-data-bucket",
        "AWS_AUDIO_BUCKET": "mock-audio-bucket",
        "G_KEY": "mock-g-key",
        "OPENAI_API_KEY": "mock-openai-key",
        "XI_KEY": "mock-xi-key",
        "FFMPEG_BINARY": "ffmpeg",
        "FFMPEG_PATH": "ffmpeg",
        "SIMILARITY_BOOST": "0.7",
        "STABILITY": "0.3",
        "STYLE": "0.3",
        "VOICE_ID": "mock-voice-id",
        "GEMINI_SAFETY_LEVEL": "BLOCK_NONE"
    }

    with patch.dict(os.environ, env_vars):
        # Mock AWS boto3
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            try:
                # Import lambda_function (it will import settings which checks env vars)
                from lambda_function import lambda_handler
                from src.services.gemini_service import GeminiAIService
                from src.handlers.lambda_handler import LambdaHandler
                from src.config.settings import settings

                # Explicitly set settings
                settings.GEMINI_API_KEY = "mock-g-key"

                # Load test event
                event_path = os.path.join(os.path.dirname(__file__), '../test-requests/summary-request.json')
                with open(event_path, 'r') as f:
                    event = json.load(f)

                context = MagicMock()

                print(f"Loaded event from {event_path}")

                # Mock AI Service
                mock_ai_service = MagicMock(spec=GeminiAIService)
                mock_ai_service.analyze_sentiment.return_value = json.dumps({
                    "sentiment_label": "Positive",
                    "intensity": "High",
                    "speech_to_text": "NotAvailable",
                    "added_text": "I had a peaceful day.",
                    "summary": "This is a mocked summary.",
                    "user_summary": "You had a peaceful day.",
                    "user_short_summary": "Peaceful day"
                })

                # Patch the _get_handler function
                with patch('src.handlers.lambda_handler._get_handler') as mock_get_handler:
                    # Create a handler with our mocked AI service
                    handler_instance = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
                    mock_get_handler.return_value = handler_instance

                    print("Invoking lambda_handler...")
                    response = lambda_handler(event, context)

                    print("Response received:")
                    print(json.dumps(response, indent=2))

                    # Verify response structure
                    if response['statusCode'] == 200:
                        # Check body structure based on actual response
                        # The actual response body is a JSON string representing SummaryResponse
                        body = json.loads(response['body'])

                        # Check for key fields in SummaryResponse
                        required_fields = ['request_id', 'user_id', 'inference_type', 'sentiment_label']
                        if all(field in body for field in required_fields):
                             print("✓ Verification Successful: Valid response received.")
                             return True
                        else:
                            print(f"✗ Verification Failed: Missing fields. Got keys: {list(body.keys())}")
                            return False
                    else:
                        print(f"✗ Verification Failed: Status code {response['statusCode']}")
                        return False

            except ImportError as e:
                print(f"Error: Could not import lambda_function: {e}")
                return False
            except Exception as e:
                print(f"Execution Error: {e}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == "__main__":
    success = verify_local_execution()
    if not success:
        sys.exit(1)
