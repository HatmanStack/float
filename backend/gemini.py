import os
from dotenv import load_dotenv
import pathlib
import google.generativeai as genai
from google.generativeai.types.safety_types import HarmCategory

load_dotenv()
genai.configure(api_key=os.environ['G_KEY'])

safety_settings = {HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: 4,
                   HarmCategory.HARM_CATEGORY_HATE_SPEECH: 4,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: 4,
                     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: 4, }

model = genai.GenerativeModel(model_name="gemini-1.5-flash", safety_settings=safety_settings)

prompt_text = 'You are an AI assistant specialized in determining the sentiment\
and its intensity from provided data.\
\
Your task is to analyze the given data, which is a text string.\
Use this data to return a sentiment label from the provided labels on a scale from 1 to 5, where 5 indicates\
the strongest intensity of the emotion indicated by the data.\
\
Instructions:\
\
1. Review the provided data\
2. Determine the sentiment label using one of the 7 provided labels.\
- Provided Sentiment Labels: "Angry," "Disgusted," "Fearful," "Happy," "Neutral," "Sad," "Surprised."\
3. Assess the intensity of the identified sentiment on a scale from 1 to 5, where 5 is the strongest intensity.\
4. Provide a summary of why you selected the sentiment label and intensity score.\
5. Provide a summary of the incident to remind the user what happened and return it in First person.\
6. Provide a short summary of the incident in just a few words\
\
Return your response in the specified format as a json.\
\
Format your response as follows:\
sentiment_label: [Your sentiment label here]\
intensity: [Your intensity score here]\
speech_to_text: NotAvailable\
added_text: [The prompt that you are evaluating]\
summary: [Your summary of why you selected the sentiment label and intensity score]\
user_summary: [A summary to help remind the user what the incident was about, it should be in First person]\
user_short_summary: [A few words to describe the incident]\
\
Remember:\
\
Use all available data to make an informed determination.\
Base your response solely on the provided text.\
Ensure the sentiment label is one of the 7 provided labels.\
The intensity scale should be from 1 to 5.\
\
Here\'s the text:'

prompt_audio = 'You are an AI assistant specialized in determining the sentiment\
and its intensity from provided data.\
\
Your task is to analyze the given data, which may include an audio file.\
Use this data to return a sentiment label from the provided labels and a scale from 1 to 5, where 5 indicates\
the strongest intensity of the emotion indicated by the data.\
\
Instructions:\
\
1. Review the provided data:\
- Audio File: An audio file that may contain speech to be transcribed.\
2. Determine the sentiment label using the 7 provided labels.\
- Provided Sentiment Labels: "Angry," "Disgusted," "Fearful," "Happy," "Neutral," "Sad," "Surprised."\
3. Assess the intensity of the identified sentiment on a scale from 1 to 5, where 5 is the strongest intensity.\
4. Transcribe the text from the provided audio content.\
5. Provide a summary of why you selected the sentiment label and intensity score.\
6. Provide a summary of the incident to remind the user what happened and return it in First person.\
7. Provide a short summary of the incident in just a few words\
\
Return your response in the specified format as a json.\
\
Format your response as follows:\
sentiment_label: [Your sentiment label here]\
intensity: [Your intensity score here]\
speech_to_text: [The transcribed text that was evaluated]\
added_text: NotAvailable\
summary: [Your summary of why you selected the sentiment label and intensity score]\
user_summary: [A summary to help remind the user what the incident was about, it should be in First person]\
user_short_summary: [A few words to describe the incident]\
\
Remember:\
\
Base your response solely on the provided audio file.\
Ensure the sentiment label is one of the 7 provided labels.\
The intensity scale should be from 1 to 5.'


prompt_synthesis = 'You are an AI assistant specialized in synthesizing sentiment analysis results from both text and audio data.\
\
Your task is to combine the sentiment analysis results from two separate data sources: an audio file analysis (which includes a \
transcribed text and sentiment analysis) and a separate text prompt analysis. Use these results to return a single, unified sentiment label and intensity score.\
\
Instructions:\
\
1. Review the two provided sentiment analysis results:\
   - Sentiment analysis result from the Audio File analysis (which includes the transcribed text and sentiment analysis).\
   - Sentiment analysis result from the Separate Text Prompt analysis.\
2. Synthesize the sentiment label and intensity score from the two separate results to arrive at a single, unified analysis.\
3. Provide a unified summary of why you selected the final sentiment label and intensity score.\
4. Provide a summary of the incident to remind the user what happened, and return it in First person.\
5. Provide a short summary of the incident in just a few words.\
6. If there are entries in the added_text or speech_to_text in either response that is not \'NotAvailable\' include it in Synthesized response in the appropriate field.\
\
Return your synthesized response in the following JSON format:\
\
{\
  "sentiment_label": "[Your unified sentiment label here]",\
  "intensity": "[Your unified intensity score here]",\
  "speech_to_text": "[The transcribed text from the audio file]",\
  "added_text": "[The additional text prompt]",\
  "summary": "[Unified summary of why you selected the sentiment label and intensity score]",\
  "user_summary": "[A summary to help remind the user what the incident was about, in First person]",\
  "user_short_summary": "[A few words to describe the incident]"\
}\
\
Remember:\
\
- Use both provided sentiment analysis results to make an informed unified determination.\
- Ensure the final sentiment label is one of the 7 provided labels.\
- The intensity scale should be from 1 to 5.\
\
Here are the results from the audio and text prompts for synthesis:\
- Audio Prompt Result:'


prompt_b = 'You are a meditation guide tasked with creating a personalized meditation transcript. \
You will receive data in JSON format which includes lists of strings with the keys sentiment_label, intensity, \
speech-to-text, added_text, and summary.  Each index of the lists will refer to a different instance that was evaluated.\
Your goal is to evaluate all the data and craft a meditation script that addresses each of the instances and helps \
the user release them.  If there are specific incidents mentioned in the summaries recall them to the user to \
help them visualize the instance and release it. If there are multiple instances of data, ensure that each instance \
is acknowledged and released.\
\
JSON Data Format\
  {\
    "sentiment_label": ["<overall sentiment of the data>"],\
    "intensity": ["<evaluated intensity of the sentiment_label>"],\
    "speech_to_text": ["<if audio was used in the evaluation this is the speech-to-text output, it may be NotAvailable if there was only a text prompt>"],\
    "added_text": ["<any additional text that was evaluated, it may be NotAvailable if there was only an audio file>"],\
    "summary": ["<a summary of why the sentiment label and intensity were selected>"]\
    "user_summary":["<a summary of in First Person about the incident>"]\
    "user_short_summary":["<a summary of just a few words to describe the incident>"]\
  }\
\
Instructions:\
1. Evaluate the Data: Consider all the provided data points for each instance, including the sentiment_label, \
intensity, speech-to-text, added_text, and summary.\
2. Identify Specific Instances: Focus on specific instances mentioned in the summaries that need to be \
addressed in the meditation. \
3. Create the Meditation Transcript: Develop a meditation script that guides \
the user through releasing each identified instance. Ensure the tone is calming and supportive. \
Include pauses at relevant intervals using the format: <break time="x.xs" />.\
Example Input:\
\
  {\
    "sentiment_label": ["Angry", "Sad"],\
    "intensity": ["3", "5"],\
    "speech_to_text": ["I got into an argument with a close friend.","NotAvailable],\
    "added_text": ["NotAvailable","I feel overwhelmed by everything happening at work."],\
    "summary": ["The individual is experiencing medium intensity anger due to a recent argument with a close friend.","The individual feels a high level of sadness due to being overwhelmed at work."]\
    "user_summary":["I\'m upset about a friend","I\'m feeling down because of work" ]\
    "user_short_summary":["Domestic Friction", "Work Stress"]\
  }\
\
Example Output:\
\
Welcome to this meditation session. Take a deep breath in, and as you exhale, allow yourself to fully arrive in this moment. <break time="4.0s" />\
\
Let\'s begin by acknowledging any frustration or stress in your life. Understand that these incidents aren\'t happening to us. They are part of the world in\
the same way as rain or fresh cut grass.  <break time="7.0s" />\
Inhale deeply, and as you exhale, visualize the weight of these frustrations lifting. <break time="9.0s" /> With each breath, \
let go of any anger or tension, creating space for calm and focus. <break time="5.0s" />\
\
When we move through the world with the understanding that the world is not happening to us, our reactions become our own. <break time="7.0s" /> \
What we need to change becomes what is inside ourselves.  We learn to flow. <break time="5.0s">\
Breathe in deeply, and as you exhale, visualize tension and frustration dissolving.  <break time="5.0s" /> Let go of any need to control.  <break time="9.0s" /> \
\
Continue to breathe deeply, focusing on releasing any remaining tension or negative emotions. <break time="4.0s" /> \
Know that you have the power to let go and create a state of inner calm.  <break time="13.0s" /> \
\
When you are ready, gently bring your awareness back to the present moment.\
\
Here is the Data:'

def getSummary(audio_file, user_text):
    print('getSummary')
    call = []
    text_response = None
    audio_response = None
    response = None
    print('Audio_File', audio_file)
    print('User_Text', user_text)
    if 'NotAvailable' not in user_text:
        prompt = prompt_text + user_text
        call = [prompt]
        print('User Text:', user_text)
        text_response = model.generate_content(call) 
        print('Text Response:', text_response.text)
    if 'NotAvailable' not in audio_file: 
        audio_load = {
                "mime_type": "audio/mp3",
                "data": pathlib.Path(audio_file).read_bytes()
            }
        call = [prompt_audio,audio_load]
        audio_response = model.generate_content(call) 
        print('Audio Response:', audio_response.text)
    if text_response and audio_response:
        prompt = prompt_synthesis + audio_response.text + 'Here\'s the Text Response:' + text_response.text
        response = model.generate_content([prompt])
    elif text_response:
        response = text_response
    else:
        response = audio_response
        
    return response.text

def getMeditation(data):
    print('getMeditation')
    print('Data', str(data))
    response = model.generate_content([prompt_b + str(data)])
    return response.text
