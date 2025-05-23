import * as Notifications from 'expo-notifications';
import { Platform } from "react-native";

const LAMBDA_FUNCTION_URL = process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL;

export async function BackendSummaryCall(
  recordingURI: any,
  separateTextPrompt: string,
  user: string
) {
  if (LAMBDA_FUNCTION_URL === 'YOUR_LAMBDA_FUNCTION_URL_HERE') {
    const errorMessage = "FATAL: LAMBDA_FUNCTION_URL is not set. Please update it in BackendSummaryCall.";
    console.error(errorMessage);
    throw new Error(errorMessage);
  }

  const payload = {
    inference_type: "summary",
    audio: recordingURI ? recordingURI : "NotAvailable",
    prompt:
      separateTextPrompt && separateTextPrompt.length > 0
        ? separateTextPrompt
        : "NotAvailable",
    input_data: "NotAvailable", // As per original logic
    user_id: user
  };

  const serializedData = JSON.stringify(payload);
  console.log(`Payload to Lambda: ${serializedData}`);
  try {
    console.log(`Calling Summary Lambda URL: ${LAMBDA_FUNCTION_URL}`);
    const httpResponse = await fetch(LAMBDA_FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: serializedData,
    });

    if (!httpResponse.ok) {
      const errorText = await httpResponse.text();
      const errorMessage = `Request to Summary Lambda URL failed with status ${httpResponse.status}: ${errorText}`;
      console.error(errorMessage);
      throw new Error(errorMessage);
    }

    const lambdaPrimaryResponse = await httpResponse.json();
    console.log(`Type of Lambda Response:`, typeof lambdaPrimaryResponse);
    console.log(`Lambda Response:`, lambdaPrimaryResponse);

    if (!lambdaPrimaryResponse || typeof lambdaPrimaryResponse !== 'object') {
      const errorMessage = `Invalid response structure from Lambda. Expected a 'body' string. Received: ${JSON.stringify(lambdaPrimaryResponse)}`;
      console.error(errorMessage);
      throw new Error(errorMessage);
    }

    let finalResponsePayload;
    try {
      finalResponsePayload = lambdaPrimaryResponse;
      console.log(`Parsed Lambda Response:`, finalResponsePayload);
    } catch (parseError) {
      const errorMessage = `Error parsing the inner 'body' string from Lambda response: ${parseError}. Body was: ${lambdaPrimaryResponse}`;
      console.error(errorMessage);
      throw new Error(errorMessage);
    }

    // 4. Apply post-processing logic (previously in invokeLambdaFunction)
    if (Platform.OS !== 'web') {
      // Ensure schedulePushNotification is an async function if you await it
      if (typeof schedulePushNotification === 'function') {
         finalResponsePayload.notification_id = await schedulePushNotification(finalResponsePayload.sentiment_label, finalResponsePayload.intensity);
      } else {
        console.warn("schedulePushNotification function is not available or not a function.");
      }
    }
    finalResponsePayload.timestamp = new Date().toISOString();
    finalResponsePayload.color_key = 0; // As per original logic

    return finalResponsePayload;

  } catch (error) {
    // Log the already specific error or a generic one if it's not an Error instance
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.log(`Error in BackendSummaryCall: ${errorMessage}`); // Original log style
    // Re-throw the error for the caller to handle
    throw error;
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
