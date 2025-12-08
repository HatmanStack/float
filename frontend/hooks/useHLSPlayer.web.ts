/**
 * useHLSPlayer - Web implementation using HLS.js
 * Provides HLS streaming playback for web browsers.
 * Safari uses native HLS support when available.
 */

import Hls, { Events, ErrorTypes, ErrorDetails } from 'hls.js';
import { useState, useEffect, useCallback, useRef } from 'react';

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
  const playlistUrlRef = useRef<string | null>(null);

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

  // Initialize HLS when playlist URL changes
  useEffect(() => {
    const audio = audioRef.current;

    // Handle no URL case
    if (!audio || !playlistUrl) {
      playlistUrlRef.current = playlistUrl;
      return;
    }

    // Skip if URL hasn't changed
    if (playlistUrl === playlistUrlRef.current) return;
    playlistUrlRef.current = playlistUrl;

    // Cleanup previous HLS instance
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    // Use native HLS for Safari
    if (supportsNativeHLS()) {
      audio.src = playlistUrl;
      audio.load();
      // Auto-play when ready
      audio.addEventListener('canplay', () => {
        audio.play().catch(err => {
          console.warn('Auto-play prevented:', err);
        });
      }, { once: true });
      return;
    }

    // Use HLS.js for other browsers
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

    const hls = new Hls({
      // Live streaming configuration
      liveSyncDuration: 3,
      liveMaxLatencyDuration: 10,
      liveDurationInfinity: true,
      // Enable low latency mode
      lowLatencyMode: true,
      // Retry configuration
      manifestLoadingMaxRetry: 4,
      manifestLoadingRetryDelay: 1000,
      levelLoadingMaxRetry: 4,
      levelLoadingRetryDelay: 1000,
      fragLoadingMaxRetry: 6,
      fragLoadingRetryDelay: 1000,
    });

    hlsRef.current = hls;

    hls.on(Events.MANIFEST_PARSED, () => {
      setState(prev => ({ ...prev, isLoading: false }));
      // Auto-play when manifest is parsed
      audio.play().catch(err => {
        console.warn('Auto-play prevented:', err);
      });
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
        switch (data.type) {
          case ErrorTypes.NETWORK_ERROR:
            // Try to recover from network errors
            hls.startLoad();
            break;
          case ErrorTypes.MEDIA_ERROR:
            // Try to recover from media errors
            hls.recoverMediaError();
            break;
          default:
            // Cannot recover
            setState(prev => ({
              ...prev,
              isLoading: false,
              error: new Error(`HLS fatal error: ${data.details}`),
            }));
            hls.destroy();
            break;
        }
      } else {
        // Non-fatal errors - HLS.js will handle retry
        if (data.details === ErrorDetails.BUFFER_STALLED_ERROR) {
          setState(prev => ({ ...prev, isLoading: true }));
        }
      }
    });

    hls.loadSource(playlistUrl);
    hls.attachMedia(audio);

    return () => {
      hls.destroy();
      hlsRef.current = null;
    };
  }, [playlistUrl, supportsNativeHLS]);

  // Controls
  const play = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.play().catch(err => {
        console.error('Play error:', err);
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
    const url = playlistUrlRef.current;

    if (!audio || !url) return;

    // Cleanup existing HLS
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    // Force URL change to trigger re-initialization
    playlistUrlRef.current = null;

    // Small delay then re-set URL to trigger effect
    setTimeout(() => {
      playlistUrlRef.current = url;

      if (supportsNativeHLS()) {
        audio.src = url;
        audio.load();
        audio.play().catch(console.warn);
        return;
      }

      if (Hls.isSupported()) {
        const hls = new Hls({
          liveSyncDuration: 3,
          liveMaxLatencyDuration: 10,
          liveDurationInfinity: true,
          lowLatencyMode: true,
        });
        hlsRef.current = hls;

        hls.on(Events.MANIFEST_PARSED, () => {
          setState(prev => ({ ...prev, isLoading: false }));
          audio.play().catch(console.warn);
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

        hls.loadSource(url);
        hls.attachMedia(audio);
      }
    }, 100);
  }, [supportsNativeHLS]);

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
