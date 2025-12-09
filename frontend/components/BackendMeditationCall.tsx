import * as FileSystem from 'expo-file-system';
import { Platform } from 'react-native';
import type {
  JobStatusResponse,
  MeditationResult,
  StreamingInfo,
} from '@/types/api';

/**
 * Incident data structure
 */
interface IncidentData {
  sentiment_label?: string;
  intensity?: number | string;
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
 * Meditation response structure (legacy format for backward compatibility)
 */
export interface MeditationResponse {
  responseMeditationURI: string | null;
  responseMusicList: string[];
}

/**
 * Streaming meditation response with HLS support
 */
export interface StreamingMeditationResponse {
  jobId: string;
  playlistUrl: string | null;
  isStreaming: boolean;
  waitForCompletion: () => Promise<MeditationResult>;
  getDownloadUrl: () => Promise<string>;
  // Legacy fields for compatibility
  responseMeditationURI: string | null;
  responseMusicList: string[];
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
    if (d.intensity !== undefined) {
      const intensityNum = typeof d.intensity === 'string' ? parseInt(d.intensity, 10) : d.intensity;
      transformedDict.intensity.push(intensityNum);
    }
    if (d.speech_to_text) transformedDict.speech_to_text.push(d.speech_to_text);
    if (d.added_text) transformedDict.added_text.push(d.added_text);
    if (d.summary) transformedDict.summary.push(d.summary);
  });
  return transformedDict;
};

const LAMBDA_FUNCTION_URL = process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL || '';

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
 * Poll for job status until streaming starts, completed, or failed.
 * Returns early when streaming begins to allow immediate playback.
 */
async function pollJobStatusForStreaming(
  jobId: string,
  userId: string,
  lambdaUrl: string,
  onStatusUpdate?: (status: JobStatusResponse) => void
): Promise<JobStatusResponse> {
  const baseUrl = lambdaUrl.replace(/\/$/, '');
  const statusUrl = `${baseUrl}/job/${jobId}?user_id=${encodeURIComponent(userId)}`;

  const startTime = Date.now();
  let pollInterval = INITIAL_POLL_INTERVAL_MS;

  while (Date.now() - startTime < MAX_TOTAL_WAIT_MS) {
    const response = await fetch(statusUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Job status check failed with status ${response.status}`);
    }

    const jobData: JobStatusResponse = await response.json();
    onStatusUpdate?.(jobData);

    // Return early when streaming starts OR when completed
    if (jobData.status === 'streaming' && jobData.streaming?.playlist_url) {
      return jobData;
    }

    if (jobData.status === 'completed') {
      return jobData;
    }

    if (jobData.status === 'failed') {
      const errorMsg = typeof jobData.error === 'string'
        ? jobData.error
        : jobData.error?.message || 'Meditation generation failed';
      throw new Error(errorMsg);
    }

    // Wait with exponential backoff before next poll
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
    pollInterval = getNextPollInterval(pollInterval);
  }

  throw new Error('Meditation generation timed out');
}

/**
 * Continue polling until job is fully completed.
 * Used after streaming starts to detect when download is available.
 */
async function pollUntilComplete(
  jobId: string,
  userId: string,
  lambdaUrl: string,
  onStatusUpdate?: (status: JobStatusResponse) => void
): Promise<JobStatusResponse> {
  const baseUrl = lambdaUrl.replace(/\/$/, '');
  const statusUrl = `${baseUrl}/job/${jobId}?user_id=${encodeURIComponent(userId)}`;

  const startTime = Date.now();
  let pollInterval = INITIAL_POLL_INTERVAL_MS;

  while (Date.now() - startTime < MAX_TOTAL_WAIT_MS) {
    const response = await fetch(statusUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Job status check failed with status ${response.status}`);
    }

    const jobData: JobStatusResponse = await response.json();
    onStatusUpdate?.(jobData);

    if (jobData.status === 'completed') {
      return jobData;
    }

    if (jobData.status === 'failed') {
      const errorMsg = typeof jobData.error === 'string'
        ? jobData.error
        : jobData.error?.message || 'Meditation generation failed';
      throw new Error(errorMsg);
    }

    // Wait with exponential backoff before next poll
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
    pollInterval = getNextPollInterval(pollInterval);
  }

  throw new Error('Meditation generation timed out');
}

/**
 * Fetch download URL for completed meditation.
 */
async function fetchDownloadUrl(
  jobId: string,
  userId: string,
  lambdaUrl: string
): Promise<string> {
  const baseUrl = lambdaUrl.replace(/\/$/, '');
  const downloadUrl = `${baseUrl}/job/${jobId}/download?user_id=${encodeURIComponent(userId)}`;

  const response = await fetch(downloadUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Download request failed with status ${response.status}`);
  }

  const data = await response.json();

  // Validate response contains download URL
  if (!data.download_url) {
    const errorMsg = data.error?.message || 'No download URL returned';
    throw new Error(errorMsg);
  }

  return data.download_url;
}

/**
 * Legacy poll for job status until completed or failed.
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

  while (Date.now() - startTime < MAX_TOTAL_WAIT_MS) {

    const response = await fetch(statusUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Job status check failed with status ${response.status}`);
    }

    const jobData: JobStatusResponse = await response.json();

    if (jobData.status === 'completed') {
      return jobData;
    }

    if (jobData.status === 'failed') {
      const errorMsg = typeof jobData.error === 'string'
        ? jobData.error
        : jobData.error?.message || 'Meditation generation failed';
      throw new Error(errorMsg);
    }

    // Wait with exponential backoff before next poll
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
    pollInterval = getNextPollInterval(pollInterval);
  }

  throw new Error('Meditation generation timed out');
}

/**
 * Convert streaming info to MeditationResult
 */
function toMeditationResult(jobData: JobStatusResponse): MeditationResult {
  return {
    jobId: jobData.job_id,
    playlistUrl: jobData.streaming?.playlist_url,
    isStreaming: jobData.status === 'streaming' || !!jobData.streaming,
    segmentsCompleted: jobData.streaming?.segments_completed ?? 0,
    segmentsTotal: jobData.streaming?.segments_total ?? null,
    isComplete: jobData.status === 'completed',
    downloadAvailable: jobData.download?.available ?? false,
  };
}

/**
 * Streaming meditation call with HLS support.
 * Returns immediately when streaming starts, with functions to wait for completion.
 */
export async function BackendMeditationCallStreaming(
  selectedIndexes: number[],
  resolvedIncidents: IncidentData[],
  musicList: string[],
  userId: string,
  lambdaUrl: string = LAMBDA_FUNCTION_URL,
  onStatusUpdate?: (status: JobStatusResponse) => void
): Promise<StreamingMeditationResponse> {
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

    if (!submitResponse.job_id) {
      throw new Error('No job_id returned from meditation request');
    }

    const jobId = submitResponse.job_id;

    // Step 2: Poll until streaming starts or completed
    const initialStatus = await pollJobStatusForStreaming(jobId, userId, lambdaUrl, onStatusUpdate);

    // Check if this is a streaming job
    const isStreaming = initialStatus.status === 'streaming' || !!initialStatus.streaming;
    const playlistUrl = initialStatus.streaming?.playlist_url || null;

    // Create continuation functions
    const waitForCompletion = async (): Promise<MeditationResult> => {
      if (initialStatus.status === 'completed') {
        return toMeditationResult(initialStatus);
      }
      const finalStatus = await pollUntilComplete(jobId, userId, lambdaUrl, onStatusUpdate);
      return toMeditationResult(finalStatus);
    };

    const getDownloadUrl = async (): Promise<string> => {
      // Ensure job is completed first
      if (initialStatus.status !== 'completed') {
        await pollUntilComplete(jobId, userId, lambdaUrl, onStatusUpdate);
      }
      return fetchDownloadUrl(jobId, userId, lambdaUrl);
    };

    // Handle non-streaming (base64 fallback) case
    let responseMeditationURI: string | null = null;
    const responseMusicList: string[] = [];

    if (!isStreaming && initialStatus.status === 'completed' && initialStatus.result?.base64) {
      responseMeditationURI = await saveResponseBase64(initialStatus.result.base64);
      responseMusicList.push(...(initialStatus.result.music_list || []));
    }

    return {
      jobId,
      playlistUrl,
      isStreaming,
      waitForCompletion,
      getDownloadUrl,
      responseMeditationURI,
      responseMusicList,
    };
  } catch (error) {
    console.error(`An error occurred in BackendMeditationCallStreaming:`, error);
    throw error;
  }
}

/**
 * Legacy meditation call (for backward compatibility).
 * Waits for full completion before returning.
 */
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

    if (!submitResponse.job_id) {
      throw new Error('No job_id returned from meditation request');
    }

    // Step 2: Poll for job completion
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
      const url = URL.createObjectURL(blob);
      return url;
    }
    const filePath = `${FileSystem.documentDirectory}output.mp3`;
    await FileSystem.writeAsStringAsync(filePath, responsePayload, {
      encoding: FileSystem.EncodingType.Base64,
    });
    return filePath;
  } catch (error) {
    console.error('Error handling the audio file:', error);
    throw error;
  }
};

// Re-export types for consumers
export type { JobStatusResponse, MeditationResult, StreamingInfo };
