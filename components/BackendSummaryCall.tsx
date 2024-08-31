import AWS from "aws-sdk";
import * as Notifications from 'expo-notifications';
import { Platform } from "react-native";

export async function BackendSummaryCall(
  recordingURI: any,
  separateTextPrompt: string,
  user: string
) {
  const data = {
    inference_type: "summary",
    audio: recordingURI ? recordingURI : "NotAvailable",
    prompt:
      separateTextPrompt && separateTextPrompt.length > 0
        ? separateTextPrompt
        : "NotAvailable",
    input_data: "NotAvailable",
    user_id: user
  };

  const serializedData = JSON.stringify(data);
  
  const awsId = process.env.EXPO_PUBLIC_AWS_ID;
  const awsSecret = process.env.EXPO_PUBLIC_AWS_SECRET;
  const awsRegion = process.env.EXPO_PUBLIC_AWS_REGION;
  
  try {
    const response = await invokeLambdaFunction(
      serializedData,
      awsId,
      awsSecret,
      awsRegion
    );

    return response;
  } catch (error) {
    console.log(`Error invoking Lambda function: ${error}`);
    throw error;
  }
}

async function invokeLambdaFunction(
  serializedData: string,
  awsId: string,
  awsSecret: string,
  awsRegion: string
) {
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

    const data = await new Promise((resolve, reject) => {
      lambda.invoke(params, (err, data) => {
        if (err) {
          reject(err);
        } else {
          resolve(data);
        }
      });
    });
    
    const responsePayloadString = JSON.parse(data.Payload).body;
    
    let responsePayload;
    try {
        // Directly parse the JSON string
        responsePayload = JSON.parse(responsePayloadString);
        
    } catch (error) {
        console.log(`Error parsing responsePayload: ${error}`);
        throw error;
    }
    if (Platform.OS !== 'web') {
      responsePayload.notification_id = await schedulePushNotification(responsePayload.sentiment_label, responsePayload.intensity);
    }
    responsePayload.timestamp = new Date().toISOString();
    responsePayload.color_key = 0;
    return responsePayload;
  } catch (e) {
    console.log(`Error handling lambda invocation: ${e}`);
    throw e;
  }
}

async function schedulePushNotification(sentiment, intensity) {
  const time_to_wait = ((38 * parseInt(intensity, 10))/4) * 60 * 60;
  
  const notificationId = await Notifications.scheduleNotificationAsync({
    content: {
      title: "Are you still ${sentiment}?",
      body: 'Float',
      data: { data: 'goes here' },
    },
    trigger: { seconds: time_to_wait  }, // Schedule to trigger in 10 seconds
  });
  return notificationId;
}
