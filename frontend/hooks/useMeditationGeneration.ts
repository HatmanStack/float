/**
 * Meditation job polling helpers.
 *
 * Phase 4 Task 4 of the 2026-04-08-audit-float plan extracted these polling
 * primitives from `BackendMeditationCall.tsx` so the high-level submission
 * module can stay under the 250-line component-file guardrail and so the
 * polling contract can be tested in isolation.
 *
 * Named `useMeditationGeneration.ts` to match the plan's file layout even
 * though the exported helpers are plain async functions rather than React
 * hooks. The backend-meditation surface is a plain TypeScript module
 * (not a React component), so no `useState`/`useEffect` wrapper is
 * needed; the module can be promoted to a true hook later without
 * breaking callers.
 */

import type { JobStatusResponse, MeditationResult } from '@/types/api';

// Polling configuration
export const INITIAL_POLL_INTERVAL_MS = 1000;
export const MAX_POLL_INTERVAL_MS = 3000;
export const MAX_TOTAL_WAIT_MS = 5 * 60 * 1000;

// Fast polling for first 45 seconds when streaming is expected
export const FAST_POLL_WINDOW_MS = 45000;
export const FAST_POLL_INTERVAL_MS = 1000;

/**
 * Calculate next poll interval.
 * Uses fast 1-second polling for first 45 seconds, then 3-second intervals.
 */
export function getNextPollInterval(elapsedMs: number): number {
  if (elapsedMs < FAST_POLL_WINDOW_MS) {
    return FAST_POLL_INTERVAL_MS;
  }
  return MAX_POLL_INTERVAL_MS;
}

export interface PollOptions {
  jobId: string;
  userId: string;
  lambdaUrl: string;
  onStatusUpdate?: (status: JobStatusResponse) => void;
  signal?: AbortSignal;
  /** Return early when streaming playlist_url is available */
  returnOnStreaming?: boolean;
}

/**
 * Poll for job status until completed, failed, or (optionally) streaming.
 * Supports cancellation via AbortSignal and adaptive polling intervals.
 */
export async function pollJobStatus(options: PollOptions): Promise<JobStatusResponse> {
  const { jobId, userId, lambdaUrl, onStatusUpdate, signal, returnOnStreaming = false } = options;
  const baseUrl = lambdaUrl.replace(/\/$/, '');
  const statusUrl = `${baseUrl}/job/${jobId}?user_id=${encodeURIComponent(userId)}`;

  const startTime = Date.now();
  let pollInterval = INITIAL_POLL_INTERVAL_MS;

  while (Date.now() - startTime < MAX_TOTAL_WAIT_MS) {
    if (signal?.aborted) {
      throw new DOMException('Polling cancelled', 'AbortError');
    }

    const fetchOptions: RequestInit = {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    };
    if (signal) {
      fetchOptions.signal = signal;
    }

    const response = await fetch(statusUrl, fetchOptions);

    if (!response.ok) {
      throw new Error(`Job status check failed with status ${response.status}`);
    }

    const jobData: JobStatusResponse = await response.json();
    onStatusUpdate?.(jobData);

    if (jobData.status === 'failed') {
      const errorMsg =
        typeof jobData.error === 'string'
          ? jobData.error
          : jobData.error?.message || 'Meditation generation failed';
      throw new Error(errorMsg);
    }

    if (returnOnStreaming && jobData.streaming?.playlist_url) {
      return jobData;
    }

    if (jobData.status === 'completed') {
      return jobData;
    }

    const elapsed = Date.now() - startTime;
    pollInterval = getNextPollInterval(elapsed);
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(resolve, pollInterval);
      if (signal) {
        signal.addEventListener(
          'abort',
          () => {
            clearTimeout(timeout);
            reject(new DOMException('Polling cancelled', 'AbortError'));
          },
          { once: true }
        );
      }
    });
  }

  throw new Error('Meditation generation timed out');
}

/**
 * Fetch download URL for completed meditation.
 */
export async function fetchDownloadUrl(
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
 * Convert streaming info to MeditationResult
 */
export function toMeditationResult(jobData: JobStatusResponse): MeditationResult {
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
