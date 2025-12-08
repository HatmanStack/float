/**
 * API types for backend communication
 * Defines response shapes for meditation jobs with HLS streaming support
 */

/**
 * Streaming information for HLS playback
 */
export interface StreamingInfo {
  playlist_url: string;
  segments_completed: number;
  segments_total: number | null;
}

/**
 * Download availability information
 */
export interface DownloadInfo {
  available: boolean;
  url: string | null;
}

/**
 * Error response structure
 */
export interface ApiError {
  code: string;
  message: string;
  retriable?: boolean;
}

/**
 * Job status response from backend
 * Extended to support HLS streaming
 */
export interface JobStatusResponse {
  job_id: string;
  user_id: string;
  status: 'pending' | 'processing' | 'streaming' | 'completed' | 'failed';
  streaming?: StreamingInfo;
  download?: DownloadInfo;
  result?: {
    base64: string;
    music_list: string[];
  };
  error?: string | ApiError;
}

/**
 * Download endpoint response
 */
export interface DownloadResponse {
  job_id: string;
  download_url: string;
  expires_in: number;
}

/**
 * Meditation result with streaming support
 */
export interface MeditationResult {
  // Existing (for base64 fallback)
  meditationUri?: string;
  musicList?: string[];

  // New (for streaming)
  jobId: string;
  playlistUrl?: string;
  isStreaming: boolean;
  segmentsCompleted: number;
  segmentsTotal: number | null;
  isComplete: boolean;
  downloadAvailable: boolean;
}
