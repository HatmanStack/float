"""Unit tests for Pydantic models."""

import pytest
from src.models.requests import SummaryRequest, MeditationRequest, parse_request_body
from src.models.responses import (
    SummaryResponse, MeditationResponse,
    create_summary_response, create_meditation_response
)
from src.config.constants import InferenceType


@pytest.mark.unit
class TestSummaryRequestModel:
    """Test SummaryRequest model validation."""

    def test_create_with_prompt(self):
        """Test creating SummaryRequest with prompt."""
        req = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="I feel sad",
            audio="NotAvailable"
        )
        assert req.user_id == "user-123"
        assert req.prompt == "I feel sad"
        assert req.audio == "NotAvailable"
        assert req.validate() is True

    def test_create_with_both_prompt_and_audio(self):
        """Test creating SummaryRequest with both prompt and audio."""
        req = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="I feel sad",
            audio="base64audiodata"
        )
        assert req.validate() is True

    def test_validation_fails_with_both_unavailable(self):
        """Test validation fails when both prompt and audio are unavailable."""
        req = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="NotAvailable",
            audio="NotAvailable"
        )
        assert req.validate() is False

    def test_validation_passes_with_empty_audio(self):
        """Test validation passes with prompt and empty audio."""
        req = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="I feel sad",
            audio=None
        )
        assert req.validate() is True

    def test_inference_type_auto_set(self):
        """Test inference_type is auto-set to SUMMARY."""
        req = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="Test",
            audio="NotAvailable"
        )
        assert req.inference_type == InferenceType.SUMMARY


@pytest.mark.unit
class TestMeditationRequestModel:
    """Test MeditationRequest model validation."""

    def test_create_valid_meditation_request(self):
        """Test creating valid MeditationRequest."""
        input_data = {
            "sentiment_label": ["Sad", "Anxious"],
            "intensity": [4, 3],
            "speech_to_text": ["NotAvailable", "I'm worried"],
            "added_text": ["Bad day", "NotAvailable"],
            "summary": ["Work stress", "Future anxiety"],
            "user_summary": ["Had a bad day", "Worried about future"],
            "user_short_summary": ["Bad day", "Anxious"]
        }
        req = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
            input_data=input_data,
            music_list=[{"name": "ambient", "volume": 0.3}]
        )
        assert req.user_id == "user-123"
        assert req.validate() is True

    def test_meditation_with_list_input_data(self):
        """Test MeditationRequest with list of input data."""
        input_data = [
            {"sentiment_label": "Sad", "intensity": 4},
            {"sentiment_label": "Anxious", "intensity": 3}
        ]
        req = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
            input_data=input_data,
            music_list=[]
        )
        assert isinstance(req.input_data, list)
        assert req.validate() is True

    def test_inference_type_auto_set_meditation(self):
        """Test inference_type is auto-set to MEDITATION."""
        req = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
            input_data={"sentiment": "Sad"},
            music_list=[]
        )
        assert req.inference_type == InferenceType.MEDITATION

    def test_validation_fails_with_empty_input_data(self):
        """Test validation fails with empty input_data."""
        req = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
            input_data={},
            music_list=[]
        )
        assert req.validate() is False

    def test_music_list_must_be_list(self):
        """Test music_list must be a list."""
        req = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
            input_data={"sentiment": "Sad"},
            music_list=[]
        )
        assert isinstance(req.music_list, list)


@pytest.mark.unit
class TestParseRequestBody:
    """Test request body parsing."""

    def test_parse_summary_request(self):
        """Test parsing a summary request body."""
        body = {
            "inference_type": InferenceType.SUMMARY,
            "user_id": "user-123",
            "prompt": "I feel sad",
            "audio": "NotAvailable"
        }
        req = parse_request_body(body)
        assert isinstance(req, SummaryRequest)
        assert req.user_id == "user-123"

    def test_parse_meditation_request(self):
        """Test parsing a meditation request body."""
        body = {
            "inference_type": InferenceType.MEDITATION,
            "user_id": "user-123",
            "input_data": {"sentiment": "Sad"},
            "music_list": []
        }
        req = parse_request_body(body)
        assert isinstance(req, MeditationRequest)
        assert req.user_id == "user-123"

    def test_parse_missing_user_id(self):
        """Test parsing fails without user_id."""
        body = {
            "inference_type": InferenceType.SUMMARY,
            "prompt": "I feel sad",
            "audio": "NotAvailable"
        }
        with pytest.raises(ValueError):
            parse_request_body(body)


@pytest.mark.unit
class TestSummaryResponse:
    """Test SummaryResponse model."""

    def test_create_summary_response_with_factory(self):
        """Test creating a summary response using factory function."""
        summary_json = '''{
            "sentiment_label": "Sad",
            "intensity": 4,
            "speech_to_text": "NotAvailable",
            "added_text": "I had a bad day",
            "summary": "User experienced a bad day",
            "user_summary": "I had a bad day at work",
            "user_short_summary": "Bad day"
        }'''
        resp = create_summary_response(123, "user-123", summary_json)
        assert resp.request_id == 123
        assert resp.user_id == "user-123"
        assert resp.sentiment_label == "Sad"
        assert resp.intensity == 4

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        summary_json = '''{
            "sentiment_label": "Sad",
            "intensity": 4,
            "speech_to_text": "NotAvailable",
            "added_text": "I had a bad day",
            "summary": "User experienced a bad day",
            "user_summary": "I had a bad day at work",
            "user_short_summary": "Bad day"
        }'''
        resp = create_summary_response(123, "user-123", summary_json)
        resp_dict = resp.to_dict()
        assert resp_dict["request_id"] == 123
        assert resp_dict["sentiment_label"] == "Sad"
        assert resp_dict["inference_type"] == "summary"


@pytest.mark.unit
class TestMeditationResponse:
    """Test MeditationResponse model."""

    def test_create_meditation_response_with_factory(self):
        """Test creating a meditation response using factory function."""
        resp = create_meditation_response(
            request_id=123,
            user_id="user-123",
            music_list=[{"name": "ambient", "volume": 0.3}],
            base64_audio="base64audiodata"
        )
        assert resp.request_id == 123
        assert resp.user_id == "user-123"
        assert len(resp.music_list) == 1
        assert resp.base64 == "base64audiodata"

    def test_meditation_response_to_dict(self):
        """Test converting meditation response to dictionary."""
        resp = create_meditation_response(
            request_id=123,
            user_id="user-123",
            music_list=[],
            base64_audio="base64audiodata"
        )
        resp_dict = resp.to_dict()
        assert resp_dict["request_id"] == 123
        assert resp_dict["base64"] == "base64audiodata"
        assert resp_dict["inference_type"] == "meditation"

    def test_meditation_response_serialization(self):
        """Test converting meditation response to JSON."""
        resp = create_meditation_response(
            request_id=123,
            user_id="user-123",
            music_list=[],
            base64_audio="base64audiodata"
        )
        json_str = resp.to_json()
        assert "base64audiodata" in json_str
        assert "meditation" in json_str
