/**
 * HLSPlayer - Web implementation using useHLSPlayer hook
 * Provides the same interface as the mobile WebView version.
 */

import { forwardRef, useImperativeHandle, useEffect, useRef } from 'react';
import { useHLSPlayer } from '@/hooks/useHLSPlayer.web';

export interface HLSPlayerProps {
  playlistUrl: string | null;
  onPlaybackStart?: () => void;
  onPlaybackPause?: () => void;
  onPlaybackComplete?: () => void;
  onError?: (error: Error) => void;
  onTimeUpdate?: (currentTime: number, duration: number | null) => void;
  onBuffering?: (buffering: boolean) => void;
  onStreamComplete?: () => void;
  autoPlay?: boolean;
}

export interface HLSPlayerRef {
  play: () => void;
  pause: () => void;
  seek: (time: number) => void;
}

/**
 * HLS Player component for web platforms.
 * Uses the useHLSPlayer hook for HLS.js integration.
 */
const HLSPlayer = forwardRef<HLSPlayerRef, HLSPlayerProps>(({
  playlistUrl,
  onPlaybackStart,
  onPlaybackPause,
  onPlaybackComplete,
  onError,
  onTimeUpdate,
  onBuffering,
  onStreamComplete,
  autoPlay = false,
}, ref) => {
  const [state, controls] = useHLSPlayer(playlistUrl);
  const prevPlayingRef = useRef(false);
  const prevCompleteRef = useRef(false);
  const prevErrorRef = useRef<Error | null>(null);
  const prevLoadingRef = useRef(false);

  // Expose controls via ref
  useImperativeHandle(ref, () => ({
    play: controls.play,
    pause: controls.pause,
    seek: controls.seek,
  }), [controls]);

  // Auto-play when playlist loads
  useEffect(() => {
    if (autoPlay && playlistUrl && !state.isLoading && !state.isPlaying && !state.error) {
      controls.play();
    }
  }, [autoPlay, playlistUrl, state.isLoading, state.isPlaying, state.error, controls]);

  // Track state changes and fire callbacks
  useEffect(() => {
    // Playback started
    if (state.isPlaying && !prevPlayingRef.current) {
      onPlaybackStart?.();
    }
    // Playback paused (was playing, now not)
    if (!state.isPlaying && prevPlayingRef.current && !state.isComplete) {
      onPlaybackPause?.();
    }
    prevPlayingRef.current = state.isPlaying;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.isPlaying, state.isComplete]);

  useEffect(() => {
    // Stream generation completed (EXT-X-ENDLIST detected)
    // This does NOT mean playback is done - just that all segments are available
    if (state.isComplete && !prevCompleteRef.current) {
      onStreamComplete?.();
    }
    prevCompleteRef.current = state.isComplete;
  }, [state.isComplete, onStreamComplete]);

  // Track when playback actually finishes (audio ended event)
  // This is when currentTime reaches duration and isPlaying becomes false
  const prevCurrentTimeRef = useRef(0);
  useEffect(() => {
    const playbackFinished =
      state.duration &&
      state.duration > 0 &&
      state.currentTime >= state.duration - 0.5 && // Within 0.5s of end
      !state.isPlaying &&
      prevCurrentTimeRef.current > 0; // Was playing before

    if (playbackFinished) {
      onPlaybackComplete?.();
    }
    prevCurrentTimeRef.current = state.currentTime;
  }, [state.currentTime, state.duration, state.isPlaying, onPlaybackComplete]);

  useEffect(() => {
    // Error occurred
    if (state.error && state.error !== prevErrorRef.current) {
      onError?.(state.error);
    }
    prevErrorRef.current = state.error;
  }, [state.error, onError]);

  useEffect(() => {
    // Buffering state changed
    if (state.isLoading !== prevLoadingRef.current) {
      onBuffering?.(state.isLoading);
    }
    prevLoadingRef.current = state.isLoading;
  }, [state.isLoading, onBuffering]);

  useEffect(() => {
    // Time update
    onTimeUpdate?.(state.currentTime, state.duration);
  }, [state.currentTime, state.duration, onTimeUpdate]);

  // This component is invisible - audio is handled by the hook
  return null;
});

HLSPlayer.displayName = 'HLSPlayer';

export default HLSPlayer;
