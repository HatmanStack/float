import * as FileSystem from "expo-file-system";
import { Platform } from "react-native";


const getTransformedDict = (dict: any, selectedIndexes: number[]) => {
  const transformedDict = {
    sentiment_label: [],
    intensity: [],
    speech_to_text: [],
    added_text: [],
    summary: [],
  };

  dict.forEach((d: any, index: number) => {
    if (!d || !selectedIndexes.includes(index)) {
      return;
    }
    
    transformedDict.sentiment_label.push(d.sentiment_label);
    transformedDict.intensity.push(d.intensity);
    transformedDict.speech_to_text.push(d.speech_to_text);
    transformedDict.added_text.push(d.added_text);
    transformedDict.summary.push(d.summary);
  });
  return transformedDict;
};


const LAMBDA_FUNCTION_URL = process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL;

export async function BackendMeditationCall(
  selectedIndexes: number[],
  resolvedIncidents: any, // Consider defining a more specific type if possible
  musicList: any,         // Consider defining a more specific type
  user: any               // Consider defining a more specific type
) {
  let dict = resolvedIncidents;
  // Assuming getTransformedDict is a synchronous function or you await it if it's async
  if (selectedIndexes.length > 1) {
    // Ensure getTransformedDict is available in this scope
    // dict = getTransformedDict(resolvedIncidents, selectedIndexes);
    // For the purpose of this example, if getTransformedDict is not provided,
    // we'll use a placeholder or log a warning.
    // Replace with your actual implementation.
    if (typeof getTransformedDict === 'function') {
        dict = getTransformedDict(resolvedIncidents, selectedIndexes);
    } else {
        console.warn("getTransformedDict function is not available. Using resolvedIncidents directly.");
    }
  }

  const payload = {
    inference_type: "meditation",
    audio: "NotAvailable",
    prompt: "NotAvailable",
    music_list: musicList,
    input_data: dict,
    user_id: user
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
        console.error("Invalid response structure from Lambda. Expected a 'body' string.", lambdaResponseObject);
        throw new Error("Invalid response structure from Lambda.");
    }
    

    // Assuming saveResponeBase64 is an async function
    // Ensure saveResponeBase64 is available in this scope.
    // Replace with your actual implementation.
    let uri = null;
    if (typeof saveResponeBase64 === 'function') {
        uri = await saveResponeBase64(lambdaResponseObject.base64);
    } else {
        console.warn("saveResponeBase64 function is not available. URI will be null.");
    }
    
    const responseMusicList = lambdaResponseObject.music_list;
    return { responseMeditationURI: uri, responseMusicList: responseMusicList };

  } catch (error) {
    console.error(`An error occurred in BackendMeditationCall:`, error);
    throw error; // Re-throw the error to be handled by the caller
  }
}

const saveResponeBase64 = async (responsePayload: string) => {
  try {
    if (Platform.OS === "web") {
      const byteCharacters = atob(responsePayload);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "audio/mp3" });
      const url = URL.createObjectURL(blob);
      console.log("File saved successfully:", url);
      return url;
    }
      const filePath = `${FileSystem.documentDirectory}output.mp3`;
      console.log("Saving file to:", filePath);
      await FileSystem.writeAsStringAsync(filePath, responsePayload, {
        encoding: FileSystem.EncodingType.Base64,
      });
      console.log("File saved successfully:", filePath);
      return filePath;
    
  } catch (error) {
    console.error("Error handling the audio file:", error);
    throw error;
  }
};
