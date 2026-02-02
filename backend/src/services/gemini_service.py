import logging
import pathlib
from typing import Any, Dict

import google.generativeai as genai  # type: ignore
from google.generativeai.types.safety_types import (  # type: ignore
    HarmCategory,
)
from zenquotespy import random as get_random_quote

from ..config.settings import settings
from ..exceptions import AIServiceError
from ..utils.circuit_breaker import gemini_circuit, with_circuit_breaker
from .ai_service import AIService

logger = logging.getLogger(__name__)


class GeminiAIService(AIService):

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: settings.GEMINI_SAFETY_LEVEL,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: settings.GEMINI_SAFETY_LEVEL,
            HarmCategory.HARM_CATEGORY_HARASSMENT: settings.GEMINI_SAFETY_LEVEL,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: settings.GEMINI_SAFETY_LEVEL,
        }
        self._setup_prompts()

    def _setup_prompts(self):
        self.prompt_text = """You are an AI assistant specialized in determining the sentiment and its intensity from provided data.
Your task is to analyze the given data, which is a text string.
Use this data to return a sentiment label from the provided labels on a scale from 1 to 5, where 5 indicates the strongest intensity of the emotion indicated by the data.
Instructions:
1. Review the provided data
2. Determine the sentiment label using one of the 7 provided labels.
- Provided Sentiment Labels: "Angry," "Disgusted," "Fearful," "Happy," "Neutral," "Sad," "Surprised."
3. Assess the intensity of the identified sentiment on a scale from 1 to 5, where 5 is the strongest intensity.
4. Provide a summary of why you selected the sentiment label and intensity score.
5. Provide a summary of the incident to remind the user what happened and return it in First person.
6. Provide a short summary of the incident in just a few words
Return your response in the specified format as a json.
Format your response as follows:
sentiment_label: [Your sentiment label here]
intensity: [Your intensity score here]
speech_to_text: NotAvailable
added_text: [The prompt that you are evaluating]
summary: [Your summary of why you selected the sentiment label and intensity score]
user_summary: [A summary to help remind the user what the incident was about, it should be in First person]
user_short_summary: [A few words to describe the incident]
Remember:
Use all available data to make an informed determination.
Base your response solely on the provided text.
Ensure the sentiment label is one of the 7 provided labels.
The intensity scale should be from 1 to 5.
Here's the text:"""
        self.prompt_audio = """You are an AI assistant specialized in determining the sentiment and its intensity from provided data.
Your task is to analyze the given data, which may include an audio file.
Use this data to return a sentiment label from the provided labels and a scale from 1 to 5, where 5 indicates the strongest intensity of the emotion indicated by the data.
Instructions:
1. Review the provided data:
- Audio File: An audio file that may contain speech to be transcribed.
2. Determine the sentiment label using the 7 provided labels.
- Provided Sentiment Labels: "Angry," "Disgusted," "Fearful," "Happy," "Neutral," "Sad," "Surprised."
3. Assess the intensity of the identified sentiment on a scale from 1 to 5, where 5 is the strongest intensity.
4. Transcribe the text from the provided audio content.
5. Provide a summary of why you selected the sentiment label and intensity score.
6. Provide a summary of the incident to remind the user what happened and return it in First person.
7. Provide a short summary of the incident in just a few words
Return your response in the specified format as a json.
Format your response as follows:
sentiment_label: [Your sentiment label here]
intensity: [Your intensity score here]
speech_to_text: [The transcribed text that was evaluated]
added_text: NotAvailable
summary: [Your summary of why you selected the sentiment label and intensity score]
user_summary: [A summary to help remind the user what the incident was about, it should be in First person]
user_short_summary: [A few words to describe the incident]
Remember:
Base your response solely on the provided audio file.
Ensure the sentiment label is one of the 7 provided labels.
The intensity scale should be from 1 to 5."""
        self.prompt_synthesis = """You are an AI assistant specialized in synthesizing sentiment analysis results from both text and audio data.
Your task is to combine the sentiment analysis results from two separate data sources: an audio file analysis (which includes a transcribed text and sentiment analysis) and a separate text prompt analysis. Use these results to return a single, unified sentiment label and intensity score.
Instructions:
1. Review the two provided sentiment analysis results:
   - Sentiment analysis result from the Audio File analysis (which includes the transcribed text and sentiment analysis).
   - Sentiment analysis result from the Separate Text Prompt analysis.
2. Synthesize the sentiment label and intensity score from the two separate results to arrive at a single, unified analysis.
3. Provide a unified summary of why you selected the final sentiment label and intensity score.
4. Provide a summary of the incident to remind the user what happened, and return it in First person.
5. Provide a short summary of the incident in just a few words.
6. If there are entries in the added_text or speech_to_text in either response that is not 'NotAvailable' include it in Synthesized response in the appropriate field.
Return your synthesized response in the following JSON format:
{
  "sentiment_label": "[Your unified sentiment label here]",
  "intensity": "[Your unified intensity score here]",
  "speech_to_text": "[The transcribed text from the audio file]",
  "added_text": "[The additional text prompt]",
  "summary": "[Unified summary of why you selected the sentiment label and intensity score]",
  "user_summary": "[A summary to help remind the user what the incident was about, in First person]",
  "user_short_summary": "[A few words to describe the incident]"
}
Remember:
- Use both provided sentiment analysis results to make an informed unified determination.
- Ensure the final sentiment label is one of the 7 provided labels.
- The intensity scale should be from 1 to 5.
- The format of your return should be only the json. There should be no additional formatting
Here are the results from the audio and text prompts for synthesis:"""
        # Base meditation prompt template - character limit filled in dynamically
        self.prompt_meditation_template = """You are a meditation guide tasked with creating a personalized meditation transcript.
You will receive data in JSON format which includes lists of strings with the keys sentiment_label, intensity,
speech-to-text, added_text, and summary. Each index of the lists will refer to a different instance that was evaluated.
Your goal is to evaluate all the data and craft a meditation script that addresses each of the instances and helps
the user release them. If there are specific incidents mentioned in the summaries recall them to the user to
help them visualize the instance and release it. If there are multiple instances of data, ensure that each instance
is acknowledged and released.
JSON Data Format
  {{
    "user_id": <a user id>,
    "sentiment_label": ["<overall sentiment of the data>"],
    "intensity": ["<evaluated intensity of the sentiment_label>"],
    "speech_to_text": ["<if audio was used in the evaluation this is the speech-to-text output, it may be NotAvailable if there was only a text prompt>"],
    "added_text": ["<any additional text that was evaluated, it may be NotAvailable if there was only an audio file>"],
    "summary": ["<a summary of why the sentiment label and intensity were selected>"]
    "user_summary":["<a summary of in First Person about the incident>"]
    "user_short_summary":["<a summary of just a few words to describe the incident>"]
  }}
Instructions:
1. Evaluate the Data: Consider all the provided data points for each instance, including the sentiment_label,
intensity, speech-to-text, added_text, and summary.
2. Identify Specific Instances: Focus on specific instances mentioned in the summaries that need to be
addressed in the meditation.
3. Create the Meditation Transcript: Develop a meditation script that guides
the user through releasing each identified instance. Ensure the tone is calming and supportive.
Use natural pauses by writing "..." or starting new paragraphs - do NOT use SSML tags.
4. Pacing: Include FREQUENT pauses for breathing and reflection. Use "..." liberally throughout
the script (at least every 2-3 sentences). Include explicit breathing instructions like
"Take a deep breath in... and slowly release..." between major sections. The meditation should
feel spacious and unhurried, with generous silence between thoughts.
5. Thematic Inspiration: Let the following wisdom guide the tone and themes of your meditation.
"{inspirational_quote}" - {quote_author}

IMPORTANT: The meditation should be approximately {target_words} words ({target_chars} characters) to achieve
a {duration_minutes}-minute spoken meditation. This is the target length - aim to be within 10% of this target.
Return only the plain text meditation script with no markup or tags.
Data for meditation transcript:"""

        # Duration to target words/chars mapping (~150 wpm spoken + pauses for breathing)
        self.duration_targets = {
            3: {"words": 450, "chars": 2300},
            5: {"words": 750, "chars": 3800},
            10: {"words": 1500, "chars": 7500},
            15: {"words": 2250, "chars": 11000},
            20: {"words": 3000, "chars": 15000},
        }

    @with_circuit_breaker(gemini_circuit)
    def analyze_sentiment(
        self, audio_file: str | None = None, user_text: str | None = None
    ) -> str:
        """
        Analyze sentiment from audio and/or text input using Gemini.

        Args:
            audio_file: Path to audio file or None if not available
            user_text: Text input or None if not available

        Returns:
            JSON string containing sentiment analysis results

        Raises:
            AIServiceError: If sentiment analysis fails.
            CircuitBreakerOpenError: If circuit breaker is open.
        """
        logger.info("Starting sentiment analysis")
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", safety_settings=self.safety_settings
        )
        text_response = None
        audio_response = None
        logger.debug(
            "Inputs - Audio: %s, Text length: %s",
            audio_file is not None,
            len(user_text) if user_text else 0,
        )
        if user_text and "NotAvailable" not in user_text:
            try:
                prompt = self.prompt_text + user_text
                logger.debug("Generating sentiment analysis for text input")
                text_response = model.generate_content([prompt])
            except Exception as e:
                logger.error("Error generating text sentiment: %s", str(e))
                raise AIServiceError(
                    f"Failed to analyze text sentiment: {str(e)}",
                    details=str(e),
                ) from e
        if audio_file and "NotAvailable" not in audio_file:
            try:
                audio_data = pathlib.Path(audio_file).read_bytes()
                audio_load = {"mime_type": "audio/mp3", "data": audio_data}
                call = [self.prompt_audio, audio_load]
                logger.debug("Generating sentiment analysis for audio input")
                audio_response = model.generate_content(call)
            except Exception as e:
                logger.error("Error generating audio sentiment: %s", str(e))
                raise AIServiceError(
                    f"Failed to analyze audio sentiment: {str(e)}",
                    details=str(e),
                ) from e
        try:
            if text_response and audio_response:
                prompt = (
                    self.prompt_synthesis
                    + audio_response.text
                    + " Here's the Text Response: "
                    + text_response.text
                )
                logger.debug("Synthesizing text and audio sentiment results")
                response = model.generate_content([prompt])
            elif text_response:
                response = text_response
            else:
                response = audio_response
        except Exception as e:
            logger.error("Error synthesizing sentiment results: %s", str(e))
            raise AIServiceError(
                f"Failed to synthesize sentiment results: {str(e)}",
                details=str(e),
            ) from e
        return response.text  # type: ignore[no-any-return]

    def _get_inspirational_quote(self) -> tuple[str, str]:
        """Get a random inspirational quote for the meditation."""
        try:
            # zenquotespy returns: '"Quote text" — Author Name'
            quote_str = get_random_quote()
            if quote_str and "—" in quote_str:
                parts = quote_str.rsplit("—", 1)
                quote = parts[0].strip().strip('"')
                author = parts[1].strip() if len(parts) > 1 else "Unknown"
                return quote, author
            return "Peace comes from within. Do not seek it without.", "Buddha"
        except Exception as e:
            logger.warning("Failed to get quote: %s, using fallback", e)
            return "Peace comes from within. Do not seek it without.", "Buddha"

    @with_circuit_breaker(gemini_circuit)
    def generate_meditation(self, input_data: Dict[str, Any], duration_minutes: int = 5) -> str:
        """Generate a meditation script from sentiment data.

        Args:
            input_data: Dictionary containing sentiment analysis results.
            duration_minutes: Target meditation duration (3, 5, 10, 15, or 20).

        Returns:
            Generated meditation script text.

        Raises:
            AIServiceError: If meditation generation fails.
            CircuitBreakerOpenError: If circuit breaker is open.
        """
        logger.info("Starting meditation generation for %d minutes", duration_minutes)
        logger.debug("Input data keys: %s", list(input_data.keys()))

        # Get target words/chars for duration (default to 5 min if not found)
        targets = self.duration_targets.get(duration_minutes, self.duration_targets[5])

        # Get inspirational quote
        quote, author = self._get_inspirational_quote()
        logger.info("Using quote: '%s' - %s", quote[:50] + "..." if len(quote) > 50 else quote, author)

        # Build prompt with duration-specific targets
        prompt_meditation = self.prompt_meditation_template.format(
            target_words=targets["words"],
            target_chars=targets["chars"],
            duration_minutes=duration_minutes,
            inspirational_quote=quote,
            quote_author=author,
        )

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            safety_settings=self.safety_settings,
        )
        try:
            prompt = prompt_meditation + str(input_data)
            response = model.generate_content([prompt])
            meditation_text = response.text
            logger.info(
                "Generated meditation: %d words, %d chars (target: %d words for %d min)",
                len(meditation_text.split()),
                len(meditation_text),
                targets["words"],
                duration_minutes,
            )
            return meditation_text  # type: ignore[no-any-return]
        except Exception as e:
            logger.error("Error generating meditation: %s", str(e))
            raise AIServiceError(
                f"Failed to generate meditation: {str(e)}",
                details=str(e),
            ) from e
