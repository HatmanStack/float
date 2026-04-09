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

  // O(1) membership check instead of an O(n*m) ``includes`` per item.
  const selectedIndexSet = new Set(selectedIndexes);
  dict.forEach((d: IncidentData, index: number) => {
    if (!d || !selectedIndexSet.has(index)) {
      return;
    }

    // Push all five fields together so array indices stay aligned per
    // incident. If any required field is missing or the intensity is
    // non-finite, skip the whole incident rather than letting one field
    // drift ahead of the others.
    if (
      !d.sentiment_label ||
      d.intensity === undefined ||
      !d.speech_to_text ||
      !d.added_text ||
      !d.summary
    ) {
      return;
    }
    // ``Number`` is stricter than ``parseInt``: ``Number("12abc")`` is
    // NaN where ``parseInt("12abc", 10)`` is 12. The downstream
    // ``Number.isFinite`` guard then rejects all malformed values.
    // ``Number("")`` is 0 (which is finite), so we have to reject blank
    // and whitespace-only intensity strings explicitly. Trim first,
    // treat the empty trimmed string as NaN, and let the existing
    // ``Number.isFinite`` guard reject it like any other malformed
    // value (e.g., ``"abc"`` -> NaN).
    let intensityNum: number;
    if (typeof d.intensity === 'string') {
      const trimmed = d.intensity.trim();
      intensityNum = trimmed === '' ? Number.NaN : Number(trimmed);
    } else {
      intensityNum = d.intensity;
    }
    if (!Number.isFinite(intensityNum)) {
      return;
    }
    transformedDict.sentiment_label.push(d.sentiment_label);
    transformedDict.intensity.push(intensityNum);
    transformedDict.speech_to_text.push(d.speech_to_text);
    transformedDict.added_text.push(d.added_text);
    transformedDict.summary.push(d.summary);
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
    // FileSystem.documentDirectory is typed `string | null` in expo-file-system;
    // fall back to cacheDirectory and finally throw so we never produce
    // a literal "nullmeditation-..." path on devices that expose neither.
    const dir = FileSystem.documentDirectory ?? FileSystem.cacheDirectory;
    if (!dir) {
      throw new Error('No writable filesystem directory available for audio output');
    }
    const filePath = `${dir}meditation-${Date.now()}-${randomPart}.mp3`;
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

  // Submit fetch must not hang forever; the backend acknowledges async
  // meditation jobs in well under a minute, so a 30s ceiling is generous.
  const submitController = new AbortController();
  const submitTimeout = setTimeout(() => submitController.abort(), 30_000);
  try {
    let httpResponse: Response;
    try {
      httpResponse = await fetch(lambdaUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: submitController.signal,
      });
    } catch (err) {
      if ((err as { name?: string })?.name === 'AbortError') {
        throw new Error('Meditation submit timed out after 30s');
      }
      throw err;
    } finally {
      clearTimeout(submitTimeout);
    }

    if (!httpResponse.ok) {
      const errorText = await httpResponse.text();
      console.error(`BackendMeditationCall failed: ${httpResponse.status}`, errorText);
      throw new Error(`Meditation request failed with status ${httpResponse.status}`);
    }

    const submitResponse = await httpResponse.json();

    if (typeof submitResponse?.job_id !== 'string' || submitResponse.job_id.length === 0) {
      throw new Error(
        `Invalid submitResponse.job_id: expected non-empty string, got ${typeof submitResponse?.job_id}`
      );
    }

    const jobResult = await pollJobStatus({
      jobId: submitResponse.job_id,
      userId,
      lambdaUrl,
    });

    if (!jobResult?.result || typeof jobResult.result !== 'object') {
      throw new Error('Invalid jobResult.result: expected object');
    }
    if (typeof jobResult.result.base64 !== 'string' || jobResult.result.base64.length === 0) {
      throw new Error(
        `Invalid jobResult.result.base64: expected non-empty string, got ${typeof jobResult.result.base64}`
      );
    }

    const uri = await saveResponseBase64(jobResult.result.base64);
    // jobResult.result.music_list may be missing, a non-array, or an
    // array containing non-strings; coerce to a clean ``string[]``.
    const rawMusicList: unknown = jobResult.result.music_list;
    const responseMusicList: string[] = Array.isArray(rawMusicList)
      ? rawMusicList.filter((item): item is string => typeof item === 'string')
      : [];
    return { responseMeditationURI: uri, responseMusicList };
  } catch (error) {
    console.error(`An error occurred in BackendMeditationCall:`, error);
    throw error;
  }
}
