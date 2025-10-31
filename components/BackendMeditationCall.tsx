import * as FileSystem from 'expo-file-system';
import { Platform } from 'react-native';

/**
 * Incident data structure
 */
interface IncidentData {
  sentiment_label?: string;
  intensity?: number;
  speech_to_text?: string;
  added_text?: string;
  summary?: string;
}

/**
 * Transformed dictionary structure for meditation
 */
interface TransformedDict {
  sentiment_label: string[];
  intensity: number[];
  speech_to_text: string[];
  added_text: string[];
  summary: string[];
}

/**
 * Meditation response structure
 */
interface MeditationResponse {
  responseMeditationURI: string | null;
  responseMusicList: string[];
}

const getTransformedDict = (dict: IncidentData[], selectedIndexes: number[]): TransformedDict => {
  const transformedDict: TransformedDict = {
    sentiment_label: [],
    intensity: [],
    speech_to_text: [],
    added_text: [],
    summary: [],
  };

  dict.forEach((d: IncidentData, index: number) => {
    if (!d || !selectedIndexes.includes(index)) {
      return;
    }

    if (d.sentiment_label) transformedDict.sentiment_label.push(d.sentiment_label);
    if (d.intensity !== undefined) transformedDict.intensity.push(d.intensity);
    if (d.speech_to_text) transformedDict.speech_to_text.push(d.speech_to_text);
    if (d.added_text) transformedDict.added_text.push(d.added_text);
    if (d.summary) transformedDict.summary.push(d.summary);
  });
  return transformedDict;
};

const LAMBDA_FUNCTION_URL = process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL || '';

/**
 * Makes a backend call to generate meditation content based on selected incidents
 */
export async function BackendMeditationCall(
  selectedIndexes: number[],
  resolvedIncidents: IncidentData[],
  musicList: string[],
  userId: string
): Promise<MeditationResponse> {
  let dict: IncidentData[] | TransformedDict = resolvedIncidents;
  if (selectedIndexes.length > 1) {
    dict = getTransformedDict(resolvedIncidents, selectedIndexes);
  }

  const payload = {
    inference_type: 'meditation',
    audio: 'NotAvailable',
    prompt: 'NotAvailable',
    music_list: musicList,
    input_data: dict,
    user_id: userId,
  };

  try {
    const httpResponse = await fetch(LAMBDA_FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!httpResponse.ok) {
      const errorText = await httpResponse.text();
      console.error(`BackendMeditationCall failed: ${httpResponse.status}`, errorText);
      throw new Error(`Request to Lambda Function URL failed with status ${httpResponse.status}`);
    }

    // Assuming the Lambda's response (httpResponse.json()) is an object
    // that itself contains a 'body' property which is a JSON string.
    const lambdaResponseObject = await httpResponse.json();

    if (!lambdaResponseObject || typeof lambdaResponseObject !== 'object') {
      console.error(
        "Invalid response structure from Lambda. Expected a 'body' string.",
        lambdaResponseObject
      );
      throw new Error('Invalid response structure from Lambda.');
    }

    console.log('Lambda response object:', lambdaResponseObject);
    const uri = await saveResponeBase64(lambdaResponseObject.base64);
    const responseMusicList = lambdaResponseObject.music_list || [];
    return { responseMeditationURI: uri, responseMusicList: responseMusicList };
  } catch (error) {
    console.error(`An error occurred in BackendMeditationCall:`, error);
    throw error; // Re-throw the error to be handled by the caller
  }
}

/**
 * Saves base64 audio response to file system or creates blob URL
 */
const saveResponeBase64 = async (responsePayload: string): Promise<string | null> => {
  try {
    if (Platform.OS === 'web') {
      const byteCharacters = atob(responsePayload);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'audio/mp3' });
      const url = URL.createObjectURL(blob);
      console.log('File saved successfully:', url);
      return url;
    }
    const filePath = `${FileSystem.documentDirectory}output.mp3`;
    console.log('Saving file to:', filePath);
    await FileSystem.writeAsStringAsync(filePath, responsePayload, {
      encoding: FileSystem.EncodingType.Base64,
    });
    console.log('File saved successfully:', filePath);
    return filePath;
  } catch (error) {
    console.error('Error handling the audio file:', error);
    throw error;
  }
};
