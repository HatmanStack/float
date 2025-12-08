/**
 * Tests for HLSPlayer component
 * Tests the mobile WebView implementation with mocked WebView
 */

import React from 'react';
import { render, act } from '@testing-library/react-native';

// Store callbacks for test access
let storedOnMessage: ((event: { nativeEvent: { data: string } }) => void) | null = null;
let storedRef: { postMessage: (data: string) => void } | null = null;

const mockPostMessage = jest.fn();

// Mock react-native-webview
jest.mock('react-native-webview', () => {
  const React = require('react');
  const { View } = require('react-native');

  const WebView = React.forwardRef((props: {
    onMessage?: (event: { nativeEvent: { data: string } }) => void;
    testID?: string;
  }, ref: React.Ref<{ postMessage: (data: string) => void }>) => {
    // Store onMessage for test access
    storedOnMessage = props.onMessage || null;

    // Create ref object
    const refObject = { postMessage: mockPostMessage };
    storedRef = refObject;

    React.useImperativeHandle(ref, () => refObject);

    return <View testID={props.testID || 'webview'} />;
  });

  WebView.displayName = 'WebView';

  return { WebView };
});

// Import after mocking
import HLSPlayer, { HLSPlayerRef } from '@/components/HLSPlayer/HLSPlayer';

describe('HLSPlayer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    storedOnMessage = null;
    storedRef = null;
  });

  describe('rendering', () => {
    it('should render WebView', () => {
      const { getByTestId } = render(
        <HLSPlayer playlistUrl={null} />
      );

      expect(getByTestId('webview')).toBeTruthy();
    });
  });

  describe('WebView message handling', () => {
    it('should call onPlaybackStart when playing message received', () => {
      const onPlaybackStart = jest.fn();
      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" onPlaybackStart={onPlaybackStart} />
      );

      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'playing' }) }
        });
      });

      expect(onPlaybackStart).toHaveBeenCalled();
    });

    it('should call onPlaybackComplete when complete message received', () => {
      const onPlaybackComplete = jest.fn();
      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" onPlaybackComplete={onPlaybackComplete} />
      );

      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'complete' }) }
        });
      });

      expect(onPlaybackComplete).toHaveBeenCalled();
    });

    it('should call onError when error message received', () => {
      const onError = jest.fn();
      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" onError={onError} />
      );

      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'error', message: 'Test error' }) }
        });
      });

      expect(onError).toHaveBeenCalledWith(expect.any(Error));
      expect(onError.mock.calls[0][0].message).toBe('Test error');
    });

    it('should call onTimeUpdate when timeupdate message received', () => {
      const onTimeUpdate = jest.fn();
      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" onTimeUpdate={onTimeUpdate} />
      );

      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'timeupdate', currentTime: 30, duration: 180 }) }
        });
      });

      expect(onTimeUpdate).toHaveBeenCalledWith(30, 180);
    });

    it('should call onBuffering when buffering message received', () => {
      const onBuffering = jest.fn();
      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" onBuffering={onBuffering} />
      );

      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'buffering', buffering: true }) }
        });
      });

      expect(onBuffering).toHaveBeenCalledWith(true);
    });

    it('should call onStreamComplete when streamComplete message received', () => {
      const onStreamComplete = jest.fn();
      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" onStreamComplete={onStreamComplete} />
      );

      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'streamComplete' }) }
        });
      });

      expect(onStreamComplete).toHaveBeenCalled();
    });
  });

  describe('commands', () => {
    it('should send load command after ready message', () => {
      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" />
      );

      // Simulate WebView ready
      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'ready' }) }
        });
      });

      // Should have sent load command
      expect(mockPostMessage).toHaveBeenCalledWith(
        expect.stringContaining('"command":"load"')
      );
      expect(mockPostMessage).toHaveBeenCalledWith(
        expect.stringContaining('playlist.m3u8')
      );
    });

    it('should send play command when autoPlay is true', () => {
      jest.useFakeTimers();

      render(
        <HLSPlayer playlistUrl="https://example.com/playlist.m3u8" autoPlay={true} />
      );

      // Simulate WebView ready
      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'ready' }) }
        });
      });

      // Advance timer for the play delay
      act(() => {
        jest.advanceTimersByTime(200);
      });

      // Should have sent play command
      expect(mockPostMessage).toHaveBeenCalledWith(
        expect.stringContaining('"command":"play"')
      );

      jest.useRealTimers();
    });
  });

  describe('ref controls', () => {
    it('should expose play, pause, seek methods via ref', () => {
      const ref = React.createRef<HLSPlayerRef>();

      render(
        <HLSPlayer ref={ref} playlistUrl="https://example.com/playlist.m3u8" />
      );

      // Simulate WebView ready
      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'ready' }) }
        });
      });

      expect(ref.current).toBeTruthy();
      expect(typeof ref.current?.play).toBe('function');
      expect(typeof ref.current?.pause).toBe('function');
      expect(typeof ref.current?.seek).toBe('function');
    });

    it('should send pause command when pause() is called', () => {
      const ref = React.createRef<HLSPlayerRef>();

      render(
        <HLSPlayer ref={ref} playlistUrl="https://example.com/playlist.m3u8" autoPlay={false} />
      );

      // Simulate WebView ready
      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'ready' }) }
        });
      });

      jest.clearAllMocks();

      act(() => {
        ref.current?.pause();
      });

      expect(mockPostMessage).toHaveBeenCalledWith(
        expect.stringContaining('"command":"pause"')
      );
    });

    it('should send seek command with time when seek() is called', () => {
      const ref = React.createRef<HLSPlayerRef>();

      render(
        <HLSPlayer ref={ref} playlistUrl="https://example.com/playlist.m3u8" autoPlay={false} />
      );

      // Simulate WebView ready
      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'ready' }) }
        });
      });

      jest.clearAllMocks();

      act(() => {
        ref.current?.seek(45);
      });

      expect(mockPostMessage).toHaveBeenCalledWith(
        expect.stringContaining('"command":"seek"')
      );
      expect(mockPostMessage).toHaveBeenCalledWith(
        expect.stringContaining('"time":45')
      );
    });
  });

  describe('URL changes', () => {
    it('should send load command when URL changes', () => {
      const { rerender } = render(
        <HLSPlayer playlistUrl="https://example.com/playlist1.m3u8" autoPlay={false} />
      );

      // Simulate WebView ready
      act(() => {
        storedOnMessage?.({
          nativeEvent: { data: JSON.stringify({ type: 'ready' }) }
        });
      });

      jest.clearAllMocks();

      // Change URL
      rerender(
        <HLSPlayer playlistUrl="https://example.com/playlist2.m3u8" autoPlay={false} />
      );

      expect(mockPostMessage).toHaveBeenCalledWith(
        expect.stringContaining('playlist2.m3u8')
      );
    });
  });
});
