"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.exceptions import ValidationError
from src.models.requests import MeditationRequestModel, SummaryRequestModel, parse_request_body
from src.models.responses import (
    create_meditation_response,
    create_summary_response,
)
from src.utils.validation import is_valid_user_id


@pytest.mark.unit
class TestUserIdValidator:
    """Test the user_id validator helper."""

    def test_user_id_validator_accepts_simple_alphanumeric(self):
        assert is_valid_user_id("user123") is True

    def test_user_id_validator_accepts_email_format(self):
        assert is_valid_user_id("user@example.com") is True

    def test_user_id_validator_accepts_uuid_format(self):
        assert is_valid_user_id("550e8400-e29b-41d4-a716-446655440000") is True

    def test_user_id_validator_accepts_google_subject_id(self):
        assert is_valid_user_id("102536842094718340569") is True

    def test_user_id_validator_rejects_path_traversal(self):
        assert is_valid_user_id("..") is False
        assert is_valid_user_id("../etc/passwd") is False

    def test_user_id_validator_rejects_slashes(self):
        assert is_valid_user_id("user/id") is False
        assert is_valid_user_id("/abs/path") is False
        assert is_valid_user_id("foo\\bar") is False

    def test_user_id_validator_rejects_empty(self):
        assert is_valid_user_id("") is False

    def test_user_id_validator_rejects_whitespace(self):
        assert is_valid_user_id("user id") is False
        assert is_valid_user_id("user\tid") is False
        assert is_valid_user_id("user\nid") is False

    def test_user_id_validator_rejects_control_characters(self):
        assert is_valid_user_id("user\x00id") is False
        assert is_valid_user_id("user\x1fid") is False

    def test_user_id_validator_rejects_over_256_chars(self):
        assert is_valid_user_id("a" * 257) is False
        assert is_valid_user_id("a" * 256) is True


@pytest.mark.unit
class TestRequestModelUserIdValidation:
    """Test that Pydantic request models reject bad user_id values."""

    def test_summary_model_rejects_path_traversal_user_id(self):
        with pytest.raises(PydanticValidationError):
            SummaryRequestModel(
                user_id="../etc/passwd",
                inference_type="summary",
                prompt="hello",
                audio="NotAvailable",
            )

    def test_summary_model_rejects_slash_user_id(self):
        with pytest.raises(PydanticValidationError):
            SummaryRequestModel(
                user_id="a/b",
                inference_type="summary",
                prompt="hello",
                audio="NotAvailable",
            )

    def test_meditation_model_rejects_path_traversal_user_id(self):
        with pytest.raises(PydanticValidationError):
            MeditationRequestModel(
                user_id="..",
                inference_type="meditation",
                input_data={"sentiment": "Sad"},
                music_list=[],
            )

    def test_meditation_model_accepts_email_user_id(self):
        req = MeditationRequestModel(
            user_id="user@example.com",
            inference_type="meditation",
            input_data={"sentiment": "Sad"},
            music_list=[],
        )
        assert req.user_id == "user@example.com"


@pytest.mark.unit
class TestSummaryRequestModel:
    """Test SummaryRequestModel Pydantic validation."""

    def test_create_with_prompt(self):
        """Test creating SummaryRequestModel with prompt."""
        req = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="I feel sad",
            audio="NotAvailable",
        )
        assert req.user_id == "user-123"
        assert req.prompt == "I feel sad"
        assert req.audio == "NotAvailable"

    def test_create_with_both_prompt_and_audio(self):
        """Test creating SummaryRequestModel with both prompt and audio."""
        req = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="I feel sad",
            audio="base64audiodata",
        )
        assert req.user_id == "user-123"

    def test_validation_fails_with_both_unavailable(self):
        """Test validation fails when both prompt and audio are unavailable."""
        with pytest.raises(PydanticValidationError):
            SummaryRequestModel(
                user_id="user-123",
                inference_type="summary",
                prompt="NotAvailable",
                audio="NotAvailable",
            )

    def test_validation_passes_with_empty_audio(self):
        """Test validation passes with prompt and empty audio."""
        req = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="I feel sad",
            audio=None,
        )
        assert req.user_id == "user-123"

    def test_inference_type_is_summary(self):
        """Test inference_type is 'summary'."""
        req = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="Test",
            audio="NotAvailable",
        )
        assert req.inference_type == "summary"


@pytest.mark.unit
class TestMeditationRequestModel:
    """Test MeditationRequestModel Pydantic validation."""

    def test_create_valid_meditation_request(self):
        """Test creating valid MeditationRequestModel."""
        input_data = {
            "sentiment_label": ["Sad", "Anxious"],
            "intensity": [4, 3],
            "speech_to_text": ["NotAvailable", "I'm worried"],
            "added_text": ["Bad day", "NotAvailable"],
            "summary": ["Work stress", "Future anxiety"],
            "user_summary": ["Had a bad day", "Worried about future"],
            "user_short_summary": ["Bad day", "Anxious"],
        }
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data=input_data,
            music_list=["ambient"],
        )
        assert req.user_id == "user-123"

    def test_meditation_with_list_input_data(self):
        """Test MeditationRequestModel with list of input data."""
        input_data = [
            {"sentiment_label": "Sad", "intensity": 4},
            {"sentiment_label": "Anxious", "intensity": 3},
        ]
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data=input_data,
            music_list=[],
        )
        assert isinstance(req.input_data, list)

    def test_inference_type_is_meditation(self):
        """Test inference_type is 'meditation'."""
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment": "Sad"},
            music_list=[],
        )
        assert req.inference_type == "meditation"

    def test_validation_fails_with_empty_input_data(self):
        """Test validation fails with empty input_data."""
        with pytest.raises(PydanticValidationError):
            MeditationRequestModel(
                user_id="user-123",
                inference_type="meditation",
                input_data={},
                music_list=[],
            )

    def test_music_list_must_be_list(self):
        """Test music_list must be a list."""
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment": "Sad"},
            music_list=[],
        )
        assert isinstance(req.music_list, list)


@pytest.mark.unit
class TestParseRequestBody:
    """Test request body parsing."""

    def test_parse_summary_request(self):
        """Test parsing a summary request body."""
        body = {
            "inference_type": "summary",
            "user_id": "user-123",
            "prompt": "I feel sad",
            "audio": "NotAvailable",
        }
        req = parse_request_body(body)
        assert isinstance(req, SummaryRequestModel)
        assert req.user_id == "user-123"

    def test_parse_meditation_request(self):
        """Test parsing a meditation request body."""
        body = {
            "inference_type": "meditation",
            "user_id": "user-123",
            "input_data": {"sentiment": "Sad"},
            "music_list": [],
        }
        req = parse_request_body(body)
        assert isinstance(req, MeditationRequestModel)
        assert req.user_id == "user-123"

    def test_parse_missing_user_id(self):
        """Test parsing fails without user_id."""
        body = {
            "inference_type": "summary",
            "prompt": "I feel sad",
            "audio": "NotAvailable",
        }
        with pytest.raises(ValidationError):
            parse_request_body(body)


@pytest.mark.unit
class TestSummaryResponse:
    """Test SummaryResponse model."""

    def test_create_summary_response_with_factory(self):
        """Test creating a summary response using factory function."""
        summary_json = """{
            "sentiment_label": "Sad",
            "intensity": 4,
            "speech_to_text": "NotAvailable",
            "added_text": "I had a bad day",
            "summary": "User experienced a bad day",
            "user_summary": "I had a bad day at work",
            "user_short_summary": "Bad day"
        }"""
        resp = create_summary_response(123, "user-123", summary_json)
        assert resp.request_id == 123
        assert resp.user_id == "user-123"
        assert resp.sentiment_label == "Sad"
        assert resp.intensity == 4

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        summary_json = """{
            "sentiment_label": "Sad",
            "intensity": 4,
            "speech_to_text": "NotAvailable",
            "added_text": "I had a bad day",
            "summary": "User experienced a bad day",
            "user_summary": "I had a bad day at work",
            "user_short_summary": "Bad day"
        }"""
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
            base64_audio="base64audiodata",
        )
        assert resp.request_id == 123
        assert resp.user_id == "user-123"
        assert len(resp.music_list) == 1
        assert resp.base64 == "base64audiodata"

    def test_meditation_response_to_dict(self):
        """Test converting meditation response to dictionary."""
        resp = create_meditation_response(
            request_id=123, user_id="user-123", music_list=[], base64_audio="base64audiodata"
        )
        resp_dict = resp.to_dict()
        assert resp_dict["request_id"] == 123
        assert resp_dict["base64"] == "base64audiodata"
        assert resp_dict["inference_type"] == "meditation"

    def test_meditation_response_serialization(self):
        """Test converting meditation response to JSON."""
        resp = create_meditation_response(
            request_id=123, user_id="user-123", music_list=[], base64_audio="base64audiodata"
        )
        json_str = resp.to_json()
        assert "base64audiodata" in json_str
        assert "meditation" in json_str


@pytest.mark.unit
class TestMeditationRequestQATranscript:
    """Test qa_transcript field on MeditationRequestModel."""

    def test_meditation_request_with_qa_transcript(self):
        """Test creating a MeditationRequestModel with qa_transcript."""
        transcript = [
            {"role": "assistant", "text": "How are you feeling?"},
            {"role": "user", "text": "I'm stressed about work."},
        ]
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment": "Sad"},
            music_list=[],
            qa_transcript=transcript,
        )
        assert len(req.qa_transcript) == 2
        assert req.qa_transcript[0].role == "assistant"
        assert req.qa_transcript[0].text == "How are you feeling?"
        assert req.qa_transcript[1].role == "user"
        assert req.qa_transcript[1].text == "I'm stressed about work."

    def test_meditation_request_without_qa_transcript(self):
        """Test creating a MeditationRequestModel without qa_transcript."""
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment": "Sad"},
            music_list=[],
        )
        assert req.qa_transcript is None

    def test_meditation_request_to_dict_with_transcript(self):
        """Test to_dict includes qa_transcript when present."""
        transcript = [{"role": "assistant", "text": "How are you?"}]
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment": "Sad"},
            music_list=[],
            qa_transcript=transcript,
        )
        d = req.to_dict()
        assert "qa_transcript" in d
        assert d["qa_transcript"] == transcript

    def test_meditation_request_to_dict_without_transcript(self):
        """Test to_dict omits qa_transcript when None."""
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment": "Sad"},
            music_list=[],
        )
        d = req.to_dict()
        assert "qa_transcript" not in d
