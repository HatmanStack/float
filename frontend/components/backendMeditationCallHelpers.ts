import * as FileSystem from 'expo-file-system/legacy';
import { Platform } from 'react-native';
import { pollJobStatus } from '@/hooks/useMeditationGeneration';

/**
 * Backend meditation call helpers. Phase 4 revision (iteration 2) moved
 * `getTransformedDict`, the legacy `BackendMeditationCall`, and the
 * base64 file-writer out of `BackendMeditationCall.tsx` so the main
 * file could stay under the Phase 4 Task 4 <200-line target.
 */

export interface IncidentData {
  sentiment_label?: string;
  intensity?: number | string;
  speech_to_text?: string;
  added_text?: string;
  summary?: string;
}

export interface TransformedDict {
  sentiment_label: string[];
  intensity: number[];
  speech_to_text: string[];
  added_text: string[];
  summary: string[];
}

export interface MeditationResponse {
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

/**
 * Saves base64 audio response to file system or creates blob URL
 */
export const saveResponseBase64 = async (responsePayload: string): Promise<string | null> => {
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
    // Unique filename so concurrent or repeated responses do not clobber
    // each other on disk. Prefer ``crypto.randomUUID`` (RN >= 0.74, all
    // modern browsers) and fall back to ``Math.random`` only if it is
    // unavailable. ``Date.now`` provides the primary uniqueness either
    // way.
    const cryptoRef = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
    const randomPart =
      cryptoRef?.randomUUID?.().replace(/-/g, '').slice(0, 12) ??
      Math.random().toString(36).slice(2, 10);
    const filePath = `${FileSystem.documentDirectory}meditation-${Date.now()}-${randomPart}.mp3`;
    await FileSystem.writeAsStringAsync(filePath, responsePayload, {
      encoding: FileSystem.EncodingType.Base64,
    });
    return filePath;
  } catch (error) {
    console.error('Error handling the audio file:', error);
    throw error;
  }
};

/**
 * Legacy meditation call (for backward compatibility).
 * Waits for full completion before returning.
 */
export async function BackendMeditationCall(
  selectedIndexes: number[],
  resolvedIncidents: IncidentData[],
  musicList: string[],
  userId: string,
  lambdaUrl: string
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
