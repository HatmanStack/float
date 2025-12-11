/**
 * useHLSPlayer - Web implementation using HLS.js
 * Provides HLS streaming playback for web browsers.
 * Safari uses native HLS support when available.
 */

import Hls, { Events, ErrorTypes, ErrorDetails, HlsConfig } from 'hls.js';
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';

// Shared HLS.js configuration - optimized for sequential playback from start
const HLS_CONFIG: Partial<HlsConfig> = {
  // Start from beginning, not live edge
  startPosition: 0,
  // Large latency tolerance - don't jump to catch up with live edge
  liveSyncDuration: 9999,
  liveMaxLatencyDuration: 99999,
  liveDurationInfinity: false,
  lowLatencyMode: false,
  // Disable back buffer trimming to keep all segments available
  backBufferLength: Infinity,
  // Retry configuration
  manifestLoadingMaxRetry: 4,
  manifestLoadingRetryDelay: 1000,
  levelLoadingMaxRetry: 4,
  levelLoadingRetryDelay: 1000,
  fragLoadingMaxRetry: 6,
  fragLoadingRetryDelay: 1000,
};

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

/**
 * React hook for HLS.js playback on web platforms.
 * Handles initialization, state management, and cleanup.
 * Falls back to native HLS for Safari.
 *
 * @param playlistUrl - HLS playlist URL (m3u8) or null
 * @returns Tuple of [state, controls, audioElement]
 */
export function useHLSPlayer(playlistUrl: string | null): [HLSPlayerState, HLSPlayerControls, HTMLAudioElement | null] {
  const [state, setState] = useState<HLSPlayerState>({
    isLoading: false,
    isPlaying: false,
    isComplete: false,
    error: null,
    duration: null,
    currentTime: 0,
  });

  const hlsRef = useRef<Hls | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Memoize the base URL so effect only runs when stream changes
  // Presigned URLs have different signatures each time but same base path
  const baseUrl = useMemo(() => {
    if (!playlistUrl) return null;
    try {
      const parsed = new URL(playlistUrl);
      return `${parsed.origin}${parsed.pathname}`;
    } catch {
      return playlistUrl;
    }
  }, [playlistUrl]);

  // Check if browser supports HLS natively (Safari)
  const supportsNativeHLS = useCallback((): boolean => {
    if (typeof document === 'undefined') return false;
    const audio = document.createElement('audio');
    return audio.canPlayType('application/vnd.apple.mpegurl') !== '';
  }, []);

  // Initialize audio element
  useEffect(() => {
    if (typeof document === 'undefined') return;

    const audio = document.createElement('audio');
    audio.preload = 'auto';
    audioRef.current = audio;

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
        audioRef.current = null;
      }
    };
  }, []);

  // Setup audio event listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handlePlay = () => {
      setState(prev => ({ ...prev, isPlaying: true }));
    };

    const handlePause = () => {
      setState(prev => ({ ...prev, isPlaying: false }));
    };

    const handleEnded = () => {
      setState(prev => ({ ...prev, isPlaying: false, isComplete: true }));
    };

    const handleTimeUpdate = () => {
      setState(prev => ({
        ...prev,
        currentTime: audio.currentTime,
        duration: audio.duration && isFinite(audio.duration) ? audio.duration : prev.duration,
      }));
    };

    const handleLoadedMetadata = () => {
      setState(prev => ({
        ...prev,
        duration: audio.duration && isFinite(audio.duration) ? audio.duration : prev.duration,
      }));
    };

    const handleWaiting = () => {
      setState(prev => ({ ...prev, isLoading: true }));
    };

    const handleCanPlay = () => {
      setState(prev => ({ ...prev, isLoading: false }));
    };

    const handleError = () => {
      const mediaError = audio.error;
      const errorTypes = ['', 'ABORTED', 'NETWORK', 'DECODE', 'SRC_NOT_SUPPORTED'];
      console.error('Audio error:', errorTypes[mediaError?.code || 0] || mediaError?.code);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: new Error(mediaError?.message || 'Audio playback error'),
      }));
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('waiting', handleWaiting);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('waiting', handleWaiting);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('error', handleError);
    };
  }, []);

  // Initialize HLS when base URL changes (ignoring presigned URL query param changes)
  useEffect(() => {
    const audio = audioRef.current;

    // Handle no URL case - cleanup if URL removed
    if (!audio || !baseUrl || !playlistUrl) {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
      return;
    }

    // If HLS is already running for this base URL, don't reinitialize
    if (hlsRef.current) {
      return;
    }

    // Always use HLS.js - native HLS support doesn't handle presigned URLs well
    // Native Safari HLS can't properly fetch segments with AWS presigned URLs
    if (!Hls.isSupported()) {
      // Schedule state update via microtask to avoid sync setState in effect
      queueMicrotask(() => {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: new Error('HLS is not supported in this browser'),
        }));
      });
      return;
    }

    const hls = new Hls(HLS_CONFIG);

    hlsRef.current = hls;

    hls.on(Events.MANIFEST_PARSED, () => {
      setState(prev => ({ ...prev, isLoading: false }));
    });

    hls.on(Events.LEVEL_LOADED, (_, data) => {
      // Get duration from level when available (for VOD or completed live streams)
      if (data.details.totalduration) {
        setState(prev => ({
          ...prev,
          duration: data.details.totalduration,
        }));
      }
      // Detect stream completion (VOD or ended live stream)
      if (data.details.live === false) {
        // Stream has ended (EXT-X-ENDLIST present)
        setState(prev => ({ ...prev, isComplete: true }));
      }
    });

    hls.on(Events.ERROR, (_, data) => {
      if (data.fatal) {
        console.error('HLS fatal:', data.type, data.details);
        switch (data.type) {
          case ErrorTypes.NETWORK_ERROR:
            hls.startLoad();
            break;
          case ErrorTypes.MEDIA_ERROR:
            hls.recoverMediaError();
            break;
          default:
            setState(prev => ({
              ...prev,
              isLoading: false,
              error: new Error(`HLS error: ${data.details}`),
            }));
            hls.destroy();
            break;
        }
      } else if (data.details === ErrorDetails.BUFFER_STALLED_ERROR) {
        setState(prev => ({ ...prev, isLoading: true }));
      }
    });

    hls.loadSource(playlistUrl);
    hls.attachMedia(audio);

    return () => {
      hls.destroy();
      hlsRef.current = null;
    };
    // Only re-run when baseUrl changes (new stream), not when presigned URL refreshes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseUrl, supportsNativeHLS]);

  // Controls
  const play = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.play().catch(err => {
        console.error('Play failed:', err.name);
        setState(prev => ({ ...prev, error: err }));
      });
    }
  }, []);

  const pause = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
    }
  }, []);

  const seek = useCallback((time: number) => {
    const audio = audioRef.current;
    if (audio && isFinite(time)) {
      audio.currentTime = time;
    }
  }, []);

  const retry = useCallback(() => {
    // Reset state
    setState({
      isLoading: true,
      isPlaying: false,
      isComplete: false,
      error: null,
      duration: null,
      currentTime: 0,
    });

    const audio = audioRef.current;

    if (!audio || !playlistUrl) return;

    // Cleanup existing HLS
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    // Reinitialize HLS
    if (Hls.isSupported()) {
      const hls = new Hls(HLS_CONFIG);
      hlsRef.current = hls;

      hls.on(Events.MANIFEST_PARSED, () => {
        setState(prev => ({ ...prev, isLoading: false }));
      });

      hls.on(Events.LEVEL_LOADED, (_, data) => {
        if (data.details.totalduration) {
          setState(prev => ({
            ...prev,
            duration: data.details.totalduration,
          }));
        }
        if (data.details.live === false) {
          setState(prev => ({ ...prev, isComplete: true }));
        }
      });

      hls.on(Events.ERROR, (_, data) => {
        if (data.fatal) {
          setState(prev => ({
            ...prev,
            isLoading: false,
            error: new Error(`HLS error: ${data.details}`),
          }));
        }
      });

      hls.loadSource(playlistUrl);
      hls.attachMedia(audio);
    }
  }, [playlistUrl]);

  const controls: HLSPlayerControls = {
    play,
    pause,
    seek,
    retry,
  };

  // Return null for audioElement - the ref is managed internally
  // External callers should use the controls interface instead
  return [state, controls, null];
}
