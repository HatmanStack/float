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

/**
 * Job status response from backend
 */
interface JobStatusResponse {
  job_id: string;
  user_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: {
    base64: string;
    music_list: string[];
  };
  error?: string;
}

// Polling configuration with exponential backoff
const INITIAL_POLL_INTERVAL_MS = 1000; // Start with 1 second
const MAX_POLL_INTERVAL_MS = 30000; // Cap at 30 seconds
const BACKOFF_MULTIPLIER = 1.5; // Increase by 50% each time
const JITTER_FACTOR = 0.2; // Add up to 20% random jitter
const MAX_TOTAL_WAIT_MS = 5 * 60 * 1000; // 5 minutes max total wait

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

// LAMBDA_FUNCTION_URL validated at runtime in BackendMeditationCall

/**
 * Calculate next poll interval with exponential backoff and jitter.
 * Jitter helps prevent thundering herd when multiple clients poll simultaneously.
 */
function getNextPollInterval(currentInterval: number): number {
  const nextInterval = Math.min(currentInterval * BACKOFF_MULTIPLIER, MAX_POLL_INTERVAL_MS);
  // Add random jitter: interval * (1 + random(-JITTER_FACTOR, +JITTER_FACTOR))
  const jitter = nextInterval * JITTER_FACTOR * (Math.random() * 2 - 1);
  return Math.round(nextInterval + jitter);
}

/**
 * Poll for job status until completed or failed.
 * Uses exponential backoff to reduce server load and battery drain.
 */
async function pollJobStatus(
  jobId: string,
  userId: string,
  lambdaUrl: string
): Promise<JobStatusResponse> {
  const baseUrl = lambdaUrl.replace(/\/$/, '');
  const statusUrl = `${baseUrl}/job/${jobId}?user_id=${encodeURIComponent(userId)}`;

  const startTime = Date.now();
  let pollInterval = INITIAL_POLL_INTERVAL_MS;
  let attempt = 0;

  while (Date.now() - startTime < MAX_TOTAL_WAIT_MS) {
    attempt++;
    console.log(
      `Polling job ${jobId}, attempt ${attempt}, interval ${Math.round(pollInterval)}ms`
    );

    const response = await fetch(statusUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Job status check failed with status ${response.status}`);
    }

    const jobData: JobStatusResponse = await response.json();
    console.log(`Job ${jobId} status: ${jobData.status}`);

    if (jobData.status === 'completed') {
      return jobData;
    }

    if (jobData.status === 'failed') {
      throw new Error(jobData.error || 'Meditation generation failed');
    }

    // Wait with exponential backoff before next poll
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
    pollInterval = getNextPollInterval(pollInterval);
  }

  throw new Error('Meditation generation timed out');
}

export async function BackendMeditationCall(
  selectedIndexes: number[],
  resolvedIncidents: IncidentData[],
  musicList: string[],
  userId: string,
  lambdaUrl: string = LAMBDA_FUNCTION_URL
): Promise<MeditationResponse> {
  const dict = getTransformedDict(resolvedIncidents, selectedIndexes);

  const payload = {
    inference_type: 'meditation',
    audio: 'NotAvailable',
    prompt: 'NotAvailable',
    music_list: musicList,
    input_data: dict,
    user_id: userId,
  };

  try {
    // Step 1: Submit the meditation request (returns job_id immediately)
    const httpResponse = await fetch(lambdaUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!httpResponse.ok) {
      const errorText = await httpResponse.text();
      console.error(`BackendMeditationCall failed: ${httpResponse.status}`, errorText);
      throw new Error(`Meditation request failed with status ${httpResponse.status}`);
    }

    const submitResponse = await httpResponse.json();
    console.log('Meditation job submitted:', submitResponse);

    if (!submitResponse.job_id) {
      throw new Error('No job_id returned from meditation request');
    }

    // Step 2: Poll for job completion
    console.log('Polling for job completion:', submitResponse.job_id);
    const jobResult = await pollJobStatus(submitResponse.job_id, userId, lambdaUrl);

    // Step 3: Extract result and convert to URI
    if (!jobResult.result?.base64) {
      throw new Error('Job completed but no audio data returned');
    }

    const uri = await saveResponseBase64(jobResult.result.base64);
    const responseMusicList = jobResult.result.music_list || [];
    return { responseMeditationURI: uri, responseMusicList };
  } catch (error) {
    console.error(`An error occurred in BackendMeditationCall:`, error);
    throw error;
  }
}

/**
 * Saves base64 audio response to file system or creates blob URL
 */
const saveResponseBase64 = async (responsePayload: string): Promise<string | null> => {
  try {
    if (Platform.OS === 'web') {
      const byteCharacters = atob(responsePayload);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'audio/mp3' });
      const url = URL.createObjectURL(blob);      return url;
    }
    const filePath = `${FileSystem.documentDirectory}output.mp3`;    await FileSystem.writeAsStringAsync(filePath, responsePayload, {
      encoding: FileSystem.EncodingType.Base64,
    });    return filePath;
  } catch (error) {
    console.error('Error handling the audio file:', error);
    throw error;
  }
};
