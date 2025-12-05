import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

const LAMBDA_FUNCTION_URL = process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL || '';

/**
 * Notification timing configuration.
 *
 * Formula: (BASE_HOURS * intensity) / DIVISOR * SECONDS_PER_HOUR
 *
 * With BASE_HOURS=38, DIVISOR=4:
 * - Intensity 1: ~9.5 hours
 * - Intensity 2: ~19 hours
 * - Intensity 3: ~28.5 hours
 * - Intensity 4: ~38 hours
 * - Intensity 5: ~47.5 hours
 *
 * Rationale: Higher intensity emotions take longer to process,
 * so we delay the follow-up notification accordingly.
 */
const NOTIFICATION_BASE_HOURS = 38;
const NOTIFICATION_DIVISOR = 4;
const SECONDS_PER_HOUR = 60 * 60;

/**
 * Summary response structure from backend
 */
interface SummaryResponse {
  sentiment_label?: string;
  intensity?: number;
  speech_to_text?: string;
  added_text?: string;
  summary?: string;
  notification_id?: string;
  timestamp?: string;
  color_key?: number;
}

/**
 * Payload structure for summary API
 */
interface SummaryPayload {
  inference_type: 'summary';
  audio: string;
  prompt: string;
  input_data: string;
  user_id: string;
}

/**
 * Schedules a push notification based on sentiment and intensity.
 *
 * The notification timing scales with intensity - higher intensity emotions
 * get longer delays before we check back in with the user.
 */
async function schedulePushNotification(sentiment: string, intensity: number): Promise<string> {
  const timeToWait =
    ((NOTIFICATION_BASE_HOURS * intensity) / NOTIFICATION_DIVISOR) * SECONDS_PER_HOUR;

  const notificationId = await Notifications.scheduleNotificationAsync({
    content: {
      title: `Are you still ${sentiment}?`,
      body: 'Float',
      data: { sentiment, intensity },
    },
    trigger: { type: 'time' as const, seconds: Math.ceil(timeToWait) } as any,
  });
  return notificationId;
}

/**
 * Makes a backend call to process audio/text and generate summary
 * @param lambdaUrl - Optional override for the Lambda URL (mainly for testing)
 */
export async function BackendSummaryCall(
  recordingURI: string | null,
  separateTextPrompt: string,
  userId: string,
  lambdaUrl: string = LAMBDA_FUNCTION_URL
): Promise<SummaryResponse> {
  // Allow mock URLs for testing (check if URL is set and not the placeholder)
  const isValidUrl =
    lambdaUrl &&
    lambdaUrl !== 'YOUR_LAMBDA_FUNCTION_URL_HERE' &&
    (lambdaUrl.startsWith('https://') || lambdaUrl.startsWith('http://'));

  if (!isValidUrl) {
    const errorMessage =
      'FATAL: LAMBDA_FUNCTION_URL is not set. Please update it in BackendSummaryCall.';
    console.error(errorMessage);
    throw new Error(errorMessage);
  }

  const payload: SummaryPayload = {
    inference_type: 'summary',
    audio: recordingURI || 'NotAvailable',
    prompt: separateTextPrompt?.length > 0 ? separateTextPrompt : 'NotAvailable',
    input_data: 'NotAvailable',
    user_id: userId,
  };

  const serializedData = JSON.stringify(payload);
  const httpResponse = await fetch(lambdaUrl, {
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
  if (!lambdaPrimaryResponse || typeof lambdaPrimaryResponse !== 'object') {
    const errorMessage = `Invalid response structure from Lambda. Expected a 'body' string. Received: ${JSON.stringify(lambdaPrimaryResponse)}`;
    console.error(errorMessage);
    throw new Error(errorMessage);
  }

  const finalResponsePayload: SummaryResponse = lambdaPrimaryResponse;
  // Apply post-processing logic
  if (Platform.OS !== 'web') {
    if (finalResponsePayload.sentiment_label && finalResponsePayload.intensity !== undefined) {
      finalResponsePayload.notification_id = await schedulePushNotification(
        finalResponsePayload.sentiment_label,
        finalResponsePayload.intensity
      );
    }
  }

  finalResponsePayload.timestamp = new Date().toISOString();
  finalResponsePayload.color_key = 0;

  return finalResponsePayload;
}
