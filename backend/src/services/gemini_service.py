import pathlib
import google.generativeai as genai
from google.generativeai.types.safety_types import HarmCategory
from typing import Dict, Any, Optional

from .ai_service import AIService
from ..config.settings import settings

class GeminiAIService(AIService):
    """Google Gemini AI service implementation."""
    
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
        """Initialize prompt templates."""
        self.prompt_text = '''You are an AI assistant specialized in determining the sentiment and its intensity from provided data.

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

Here's the text:'''

        self.prompt_audio = '''You are an AI assistant specialized in determining the sentiment and its intensity from provided data.

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
The intensity scale should be from 1 to 5.'''

        self.prompt_synthesis = '''You are an AI assistant specialized in synthesizing sentiment analysis results from both text and audio data.

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

Here are the results from the audio and text prompts for synthesis:'''

        self.prompt_meditation = '''You are a meditation guide tasked with creating a personalized meditation transcript. 
You will receive data in JSON format which includes lists of strings with the keys sentiment_label, intensity, 
speech-to-text, added_text, and summary.  Each index of the lists will refer to a different instance that was evaluated.
Your goal is to evaluate all the data and craft a meditation script that addresses each of the instances and helps 
the user release them.  If there are specific incidents mentioned in the summaries recall them to the user to 
help them visualize the instance and release it. If there are multiple instances of data, ensure that each instance 
is acknowledged and released.

JSON Data Format
  {
    "user_id": <a user id>,
    "sentiment_label": ["<overall sentiment of the data>"],
    "intensity": ["<evaluated intensity of the sentiment_label>"],
    "speech_to_text": ["<if audio was used in the evaluation this is the speech-to-text output, it may be NotAvailable if there was only a text prompt>"],
    "added_text": ["<any additional text that was evaluated, it may be NotAvailable if there was only an audio file>"],
    "summary": ["<a summary of why the sentiment label and intensity were selected>"]
    "user_summary":["<a summary of in First Person about the incident>"]
    "user_short_summary":["<a summary of just a few words to describe the incident>"]
  }

Instructions:
1. Evaluate the Data: Consider all the provided data points for each instance, including the sentiment_label, 
intensity, speech-to-text, added_text, and summary.
2. Identify Specific Instances: Focus on specific instances mentioned in the summaries that need to be 
addressed in the meditation. 
3. Create the Meditation Transcript: Develop a meditation script that guides 
the user through releasing each identified instance. Ensure the tone is calming and supportive. 
    - Use tags to create the SSML of the meditation script
        A. Include pauses at relevant intervals using the format: <break time="XXXXms"/>.

Remember to return only the meditation script.

Data for meditation transcript:'''
    
    def analyze_sentiment(self, audio_file: Optional[str], user_text: Optional[str]) -> str:
        """
        Analyze sentiment from audio and/or text input using Gemini.
        
        Args:
            audio_file: Path to audio file or None if not available
            user_text: Text input or None if not available
            
        Returns:
            JSON string containing sentiment analysis results
        """
        print('Gemini getSummary started')
        
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", 
            safety_settings=self.safety_settings
        )
        
        text_response = None
        audio_response = None
        
        print(f'Audio_File: {audio_file}')
        print(f'User_Text: {user_text}')
        
        # Process text if available
        if user_text and 'NotAvailable' not in user_text:
            prompt = self.prompt_text + user_text
            print(f'User Text: {user_text}')
            text_response = model.generate_content([prompt])
            print(f'Text Response: {text_response.text}')
        
        # Process audio if available
        if audio_file and 'NotAvailable' not in audio_file:
            audio_load = {
                "mime_type": "audio/mp3",
                "data": pathlib.Path(audio_file).read_bytes()
            }
            call = [self.prompt_audio, audio_load]
            audio_response = model.generate_content(call)
            print(f'Audio Response: {audio_response.text}')
        
        # Synthesize responses if both are available
        if text_response and audio_response:
            prompt = (self.prompt_synthesis + audio_response.text + 
                     " Here's the Text Response: " + text_response.text)
            response = model.generate_content([prompt])
        elif text_response:
            response = text_response
        else:
            response = audio_response
        
        return response.text
    
    def generate_meditation(self, input_data: Dict[str, Any]) -> str:
        """
        Generate meditation transcript based on input data using Gemini.
        
        Args:
            input_data: Dictionary containing user data for meditation generation
            
        Returns:
            Meditation transcript text
        """
        print('Gemini getMeditation started')
        print(f'Data: {str(input_data)}')
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro-preview-05-06", 
            safety_settings=self.safety_settings
        )
        
        response = model.generate_content([self.prompt_meditation + str(input_data)])
        return response.text