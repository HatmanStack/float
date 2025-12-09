/**
 * HLSPlayer - Mobile implementation using WebView
 * Embeds HLS.js in a WebView for audio playback on iOS and Android.
 */

import React, { useRef, useCallback, useEffect, useImperativeHandle, forwardRef } from 'react';
import { StyleSheet, View } from 'react-native';
import { WebView, WebViewMessageEvent } from 'react-native-webview';
import { hlsPlayerHtml } from './hlsPlayerHtml';

// Delay before auto-play to let HLS.js initialize
const AUTOPLAY_DELAY_MS = 100;

export interface HLSPlayerProps {
  playlistUrl: string | null;
  onPlaybackStart?: () => void;
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

interface WebViewMessage {
  type: string;
  message?: string;
  currentTime?: number;
  duration?: number | null;
  buffering?: boolean;
  fatal?: boolean;
}

/**
 * HLS Player component for mobile platforms using WebView.
 * Uses HLS.js embedded in HTML for audio streaming.
 */
const HLSPlayer = forwardRef<HLSPlayerRef, HLSPlayerProps>(({
  playlistUrl,
  onPlaybackStart,
  onPlaybackComplete,
  onError,
  onTimeUpdate,
  onBuffering,
  onStreamComplete,
  autoPlay = true,
}, ref) => {
  const webViewRef = useRef<WebView>(null);
  const isReadyRef = useRef(false);
  const pendingUrlRef = useRef<string | null>(null);

  // Send command to WebView
  const sendCommand = useCallback((command: string, data: Record<string, unknown> = {}) => {
    if (webViewRef.current && isReadyRef.current) {
      webViewRef.current.postMessage(JSON.stringify({ command, ...data }));
    }
  }, []);

  // Expose controls via ref
  useImperativeHandle(ref, () => ({
    play: () => sendCommand('play'),
    pause: () => sendCommand('pause'),
    seek: (time: number) => sendCommand('seek', { time }),
  }), [sendCommand]);

  // Load playlist when URL changes
  useEffect(() => {
    if (playlistUrl) {
      if (isReadyRef.current) {
        sendCommand('load', { url: playlistUrl });
        if (autoPlay) {
          setTimeout(() => sendCommand('play'), AUTOPLAY_DELAY_MS);
        }
      } else {
        // Store URL to load when WebView is ready
        pendingUrlRef.current = playlistUrl;
      }
    }
  }, [playlistUrl, sendCommand, autoPlay]);

  // Handle messages from WebView
  const handleMessage = useCallback((event: WebViewMessageEvent) => {
    try {
      const data: WebViewMessage = JSON.parse(event.nativeEvent.data);

      switch (data.type) {
        case 'ready':
          isReadyRef.current = true;
          // Load pending URL if any
          if (pendingUrlRef.current) {
            sendCommand('load', { url: pendingUrlRef.current });
            if (autoPlay) {
              setTimeout(() => sendCommand('play'), AUTOPLAY_DELAY_MS);
            }
            pendingUrlRef.current = null;
          }
          break;

        case 'playing':
          onPlaybackStart?.();
          break;

        case 'paused':
          // No-op for now
          break;

        case 'complete':
          onPlaybackComplete?.();
          break;

        case 'timeupdate':
          onTimeUpdate?.(data.currentTime ?? 0, data.duration ?? null);
          break;

        case 'buffering':
          onBuffering?.(data.buffering ?? false);
          break;

        case 'streamComplete':
          onStreamComplete?.();
          break;

        case 'error':
          onError?.(new Error(data.message || 'Unknown playback error'));
          break;

        case 'loading':
        case 'loaded':
        case 'durationchange':
          // Informational, no action needed
          break;

        default:
          // Unknown message type
          break;
      }
    } catch (e) {
      console.error('Error parsing WebView message:', e);
    }
  }, [onPlaybackStart, onPlaybackComplete, onError, onTimeUpdate, onBuffering, onStreamComplete, sendCommand, autoPlay]);

  return (
    <View style={styles.container}>
      <WebView
        ref={webViewRef}
        source={{ html: hlsPlayerHtml }}
        style={styles.webView}
        onMessage={handleMessage}
        javaScriptEnabled={true}
        mediaPlaybackRequiresUserAction={false}
        allowsInlineMediaPlayback={true}
        scrollEnabled={false}
        bounces={false}
        originWhitelist={['*']}
        // Security settings for audio playback
        mixedContentMode="compatibility"
        allowFileAccess={true}
        // Prevent WebView from showing in UI
        pointerEvents="none"
      />
    </View>
  );
});

HLSPlayer.displayName = 'HLSPlayer';

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    width: 1,
    height: 1,
    opacity: 0,
    overflow: 'hidden',
  },
  webView: {
    flex: 1,
    backgroundColor: 'transparent',
  },
});

export default HLSPlayer;
