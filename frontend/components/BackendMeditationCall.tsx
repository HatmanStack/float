import {
  fetchDownloadUrl,
  pollJobStatus,
  toMeditationResult,
} from '@/hooks/useMeditationGeneration';
import type { JobStatusResponse, MeditationResult, StreamingInfo, QATranscript } from '@/types/api';
import {
  BackendMeditationCall,
  getTransformedDict,
  saveResponseBase64,
} from './backendMeditationCallHelpers';
import type {
  IncidentData,
  MeditationResponse,
  TransformedDict,
} from './backendMeditationCallHelpers';

// Re-export the legacy helpers so existing call sites keep working.
export { BackendMeditationCall, getTransformedDict };
export type { IncidentData, MeditationResponse, TransformedDict };

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

    const initialStatus = await pollJobStatus({
      jobId,
      userId,
      lambdaUrl,
      onStatusUpdate,
      signal,
      returnOnStreaming: true,
    });

    const isStreaming = initialStatus.status === 'streaming' || !!initialStatus.streaming;
    const playlistUrl = initialStatus.streaming?.playlist_url || null;

    const waitForCompletion = async (): Promise<MeditationResult> => {
      if (initialStatus.status === 'completed') {
        return toMeditationResult(initialStatus);
      }
      const finalStatus = await pollJobStatus({ jobId, userId, lambdaUrl, onStatusUpdate, signal });
      return toMeditationResult(finalStatus);
    };

    const getDownloadUrl = async (): Promise<string> => {
      if (initialStatus.status !== 'completed') {
        await pollJobStatus({ jobId, userId, lambdaUrl, signal });
      }
      return fetchDownloadUrl(jobId, userId, lambdaUrl);
    };

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

// Re-export API types for consumers
export type { JobStatusResponse, MeditationResult, StreamingInfo };
