/**
 * useHLSPlayer - Native mobile stub
 * On mobile platforms, HLS playback is handled via WebView component, not this hook.
 * This stub returns no-op values to allow imports on native platforms.
 */

export interface HLSPlayerState {
  isLoading: boolean;
  isPlaying: boolean;
  isComplete: boolean;
  error: Error | null;
  duration: number | null;
  currentTime: number;
}

export interface HLSPlayerControls {
  play: () => void;
  pause: () => void;
  seek: (time: number) => void;
  retry: () => void;
}

const noopState: HLSPlayerState = {
  isLoading: false,
  isPlaying: false,
  isComplete: false,
  error: null,
  duration: null,
  currentTime: 0,
};

const noopControls: HLSPlayerControls = {
  play: () => {},
  pause: () => {},
  seek: () => {},
  retry: () => {},
};

/**
 * Native stub for useHLSPlayer hook.
 * On mobile, HLS playback uses WebView component instead.
 * @param _playlistUrl - Ignored on native platforms
 * @returns Tuple of [state, controls] with no-op values
 */
export function useHLSPlayer(_playlistUrl: string | null): [HLSPlayerState, HLSPlayerControls, HTMLAudioElement | null] {
  return [noopState, noopControls, null];
}
