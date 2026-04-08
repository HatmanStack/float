import * as FileSystem from 'expo-file-system/legacy';
import { Platform } from 'react-native';
import {
  fetchDownloadUrl,
  pollJobStatus,
  toMeditationResult,
} from '@/hooks/useMeditationGeneration';
import type { JobStatusResponse, MeditationResult, StreamingInfo, QATranscript } from '@/types/api';

/**
 * Incident data structure
 */
export interface IncidentData {
  sentiment_label?: string;
  intensity?: number | string;
  speech_to_text?: string;
  added_text?: string;
  summary?: string;
}

/**
 * Transformed dictionary structure for meditation
 */
export interface TransformedDict {
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

export const getTransformedDict = (
  dict: IncidentData[],
  selectedIndexes: number[]
): TransformedDict => {
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
      const intensityNum =
        typeof d.intensity === 'string' ? parseInt(d.intensity, 10) : d.intensity;
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
 * Streaming meditation call with HLS support.
 * Returns immediately when streaming starts, with functions to wait for completion.
 *
 * @param signal - Optional AbortSignal for cancellation support. When aborted,
 *                 polling stops and throws AbortError. The backend job continues
 *                 running (cancellation is client-side only).
 */
export async function BackendMeditationCallStreaming(
  selectedIndexes: number[],
  resolvedIncidents: IncidentData[],
  musicList: string[],
  userId: string,
  lambdaUrl: string = LAMBDA_FUNCTION_URL,
  onStatusUpdate?: (status: JobStatusResponse) => void,
  durationMinutes: number = 5,
  signal?: AbortSignal,
  qaTranscript?: QATranscript
): Promise<StreamingMeditationResponse> {
  const dict = getTransformedDict(resolvedIncidents, selectedIndexes);

  const payload = {
    inference_type: 'meditation',
    audio: 'NotAvailable',
    prompt: 'NotAvailable',
    music_list: musicList,
    input_data: dict,
    user_id: userId,
    duration_minutes: durationMinutes,
    ...(qaTranscript && { qa_transcript: qaTranscript }),
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
    const initialStatus = await pollJobStatus({
      jobId,
      userId,
      lambdaUrl,
      onStatusUpdate,
      signal,
      returnOnStreaming: true,
    });

    // Check if this is a streaming job
    const isStreaming = initialStatus.status === 'streaming' || !!initialStatus.streaming;
    const playlistUrl = initialStatus.streaming?.playlist_url || null;

    // Create continuation functions (capture signal for cancellation support)
    const waitForCompletion = async (): Promise<MeditationResult> => {
      if (initialStatus.status === 'completed') {
        return toMeditationResult(initialStatus);
      }
      const finalStatus = await pollJobStatus({ jobId, userId, lambdaUrl, onStatusUpdate, signal });
      return toMeditationResult(finalStatus);
    };

    const getDownloadUrl = async (): Promise<string> => {
      // Ensure job is completed first
      // Don't pass onStatusUpdate - we don't want to re-trigger streaming UI
      if (initialStatus.status !== 'completed') {
        await pollJobStatus({ jobId, userId, lambdaUrl, signal });
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

    const jobResult = await pollJobStatus({
      jobId: submitResponse.job_id,
      userId,
      lambdaUrl,
    });

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
