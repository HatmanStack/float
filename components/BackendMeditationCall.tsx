import AWS from 'aws-sdk';
import * as FileSystem from 'expo-file-system';
import { useIncident } from '@/context/IncidentContext';

const getTransformedDict = (dict: any, selectedIndexes: number[]) => {
    const transformedDict = {
      sentiment_label: [],
      intensity: [],
      speech_to_text: [],
      added_text: [],
      summary: []
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
  }

  export async function getMeditation(selectedIndexes: number[]) {
    const { incidentList } = useIncident();
    const data_audio = {
      inference_type: "meditation",
      audio: "NotAvailable",
      prompt: "NotAvailable",
      input_data: JSON.stringify(getTransformedDict(incidentList, selectedIndexes)),
    };
  
  const serializedData = JSON.stringify(data_audio);
  const awsId = '';
  const awsSecret = '';
  const awsRegion = 'us-west-1';
  
  try {
    const lambda = new AWS.Lambda({
      accessKeyId: awsId,
      secretAccessKey: awsSecret,
      region: awsRegion,
    });
    
    const params = {
      FunctionName: 'audio-er-final',
      InvocationType: 'RequestResponse',
      Payload: serializedData,
    };
    lambda.invoke(params, (err, data) => {
      if (err) {
        console.error(`An error occurred: ${err}`);
      } else {
        const responsePayload = JSON.parse(data.Payload).body  
        return saveResponeBase64(responsePayload.toString());
      }
    });
  } catch (e) {
    console.error(`An error occurred: ${e}`);
  }
  return null;
}

const saveResponeBase64 = async (responsePayload: string) => {
  try {
  
    const splitPayload = responsePayload.split("64': b'");
    if (splitPayload.length < 2) {
      throw new Error('The responsePayload does not contain the expected "64\': b\'" delimiter');
    }
    const base64Part = splitPayload[1];
    const trimmedBase64Part = base64Part.slice(0, -2);
    
    const filePath = `${FileSystem.documentDirectory}output.mp3`;
    console.log('Saving file to:', filePath);
    await FileSystem.writeAsStringAsync(filePath, trimmedBase64Part, {
      encoding: FileSystem.EncodingType.Base64,
    });
    console.log('File saved successfully:', filePath);
    return filePath;
  
  }catch (error) {
    console.error('Error handling the audio file:', error);
    return null;
  }
}
