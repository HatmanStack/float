import AWS from "aws-sdk";
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
    console.log("Dict:", d);
    transformedDict.sentiment_label.push(d.sentiment_label);
    transformedDict.intensity.push(d.intensity);
    transformedDict.speech_to_text.push(d.speech_to_text);
    transformedDict.added_text.push(d.added_text);
    transformedDict.summary.push(d.summary);
  });
  return transformedDict;
};

export async function BackendMeditationCall(
  selectedIndexes: number[],
  resolvedIncidents,
  musicList
) {
  let dict = resolvedIncidents;
  if (selectedIndexes.length > 1) {
    dict = getTransformedDict(resolvedIncidents, selectedIndexes);
  }
  console.log("Dict:", dict);
  console.log("Music List:", musicList);
  const data_audio = {
    inference_type: "meditation",
    audio: "NotAvailable",
    prompt: "NotAvailable",
    music_list: musicList,
    input_data: dict,
  };
  console.log("Data:", data_audio);
  const serializedData = JSON.stringify(data_audio);
  const awsId = process.env.EXPO_PUBLIC_AWS_ID;
  const awsSecret = process.env.EXPO_PUBLIC_AWS_SECRET;
  const awsRegion = process.env.EXPO_PUBLIC_AWS_REGION;

  try {
    const lambda = new AWS.Lambda({
      accessKeyId: awsId,
      secretAccessKey: awsSecret,
      region: awsRegion,
    });

    const params = {
      FunctionName: "audio-er-final",
      InvocationType: "RequestResponse",
      Payload: serializedData,
    };

    const responsePayload = await new Promise((resolve, reject) => {
      lambda.invoke(params, (err, data) => {
        if (err) {
          reject(`An error occurred: ${err}`);
        } else {
          resolve(JSON.parse(data.Payload).body);
        }
      });
    });
    let correctedResponse = responsePayload
      .replace(/'/g, '"')
      .replace(/b"([^"]*)"/g, '"$1"');
    try {
      const test = JSON.parse(correctedResponse);
      const uri = await saveResponeBase64(test.base64);
      const music_list = test.music_list;
      return { responseMeditationURI: uri, responseMusicList: music_list };
    } catch (e) {
      console.error(`An error occurred: ${e}`);
    }
  } catch (e) {
    console.error(`An error occurred: ${e}`);
  }
  return null;
}

const saveResponeBase64 = async (responsePayload: string) => {
  try {
    if (Platform.OS === "web") {
      // Web platform
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
    } else {
      // Mobile platform
      const filePath = `${FileSystem.documentDirectory}output.mp3`;
      console.log("Saving file to:", filePath);
      await FileSystem.writeAsStringAsync(filePath, responsePayload, {
        encoding: FileSystem.EncodingType.Base64,
      });
      console.log("File saved successfully:", filePath);
      return filePath;
    }
  } catch (error) {
    console.error("Error handling the audio file:", error);
    return null;
  }
};
