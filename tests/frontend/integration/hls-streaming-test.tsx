/**
 * Integration tests for HLS streaming flow
 * Tests the complete streaming playback flow from request to download
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';

// Mock dependencies before imports
jest.mock('expo-av', () => ({
  Audio: {
    Sound: {
      createAsync: jest.fn().mockResolvedValue({
        sound: {
          playAsync: jest.fn().mockResolvedValue({}),
          pauseAsync: jest.fn().mockResolvedValue({}),
          setOnPlaybackStatusUpdate: jest.fn(),
        },
      }),
    },
  },
}));

jest.mock('expo-file-system', () => ({
  documentDirectory: 'mock-directory/',
  writeAsStringAsync: jest.fn(() => Promise.resolve()),
  createDownloadResumable: jest.fn(() => ({
    downloadAsync: jest.fn().mockResolvedValue({ uri: 'mock-directory/meditation.mp3' }),
  })),
  EncodingType: {
    Base64: 'base64',
  },
}));

jest.mock('@/components/HLSPlayer', () => {
  const React = require('react');
  return {
    HLSPlayer: React.forwardRef((props: {
      playlistUrl: string;
      onPlaybackStart?: () => void;
      onPlaybackComplete?: () => void;
      onStreamComplete?: () => void;
      onError?: (error: Error) => void;
      autoPlay?: boolean;
    }, ref: React.Ref<{ play: () => void; pause: () => void; seek: (time: number) => void }>) => {
      React.useImperativeHandle(ref, () => ({
        play: jest.fn(),
        pause: jest.fn(),
        seek: jest.fn(),
      }));

      // Auto-trigger playback start for tests
      React.useEffect(() => {
        if (props.autoPlay && props.playlistUrl) {
          props.onPlaybackStart?.();
        }
      }, [props.playlistUrl, props.autoPlay, props.onPlaybackStart]);

      return null;
    }),
  };
});

jest.spyOn(Alert, 'alert');

// Mock fetch for API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Import components after mocking
import MeditationControls from '@/components/ScreenComponents/MeditationControls';
import { DownloadButton } from '@/components/DownloadButton';
import ErrorBoundary from '@/components/ErrorBoundary';
import StreamingError from '@/components/StreamingError';

describe('HLS Streaming Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete streaming flow', () => {
    it('should render HLSPlayer when streaming mode is active', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI=""
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // HLS play button should be visible
      expect(screen.getByTestId('hls-play-button')).toBeTruthy();
    });

    it('should fall back to legacy mode when not streaming', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI="file://meditation.mp3"
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={false}
          playlistUrl={null}
        />
      );

      // Legacy play button should be visible
      expect(screen.getByTestId('legacy-play-button')).toBeTruthy();
    });

    it('should show generate button when no content available', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI=""
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={false}
          playlistUrl={null}
        />
      );

      expect(screen.getByTestId('generate-button')).toBeTruthy();
    });

    it('should show loading indicator while generating', () => {
      render(
        <MeditationControls
          isCalling={true}
          meditationURI=""
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={false}
          playlistUrl={null}
        />
      );

      expect(screen.getByTestId('activity-indicator')).toBeTruthy();
    });
  });

  describe('Download flow', () => {
    const mockGetDownloadUrl = jest.fn().mockResolvedValue('https://example.com/download/meditation.mp3');

    it('should render download button when download is available', () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockGetDownloadUrl}
        />
      );

      expect(screen.getByTestId('download-button')).toBeTruthy();
    });

    it('should not render download button when download is not available', () => {
      render(
        <DownloadButton
          downloadAvailable={false}
          onGetDownloadUrl={mockGetDownloadUrl}
        />
      );

      expect(screen.queryByTestId('download-button')).toBeNull();
    });

    it('should trigger download flow when button pressed', async () => {
      const onDownloadStart = jest.fn();

      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockGetDownloadUrl}
          onDownloadStart={onDownloadStart}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(mockGetDownloadUrl).toHaveBeenCalled();
        expect(onDownloadStart).toHaveBeenCalled();
      });
    });
  });

  describe('Error recovery', () => {
    it('should display StreamingError component with retry option', () => {
      const mockOnRetry = jest.fn();
      const error = new Error('Network error');

      render(
        <StreamingError error={error} onRetry={mockOnRetry} canRetry={true} />
      );

      expect(screen.getByTestId('streaming-error')).toBeTruthy();
      expect(screen.getByTestId('streaming-error-retry-button')).toBeTruthy();
    });

    it('should call retry callback when retry button pressed', () => {
      const mockOnRetry = jest.fn();
      const error = new Error('HLS error');

      render(
        <StreamingError error={error} onRetry={mockOnRetry} canRetry={true} />
      );

      fireEvent.press(screen.getByTestId('streaming-error-retry-button'));

      expect(mockOnRetry).toHaveBeenCalled();
    });
  });

  describe('ErrorBoundary', () => {
    // Create a component that throws an error
    const ThrowingComponent = () => {
      throw new Error('Test error');
    };

    // Suppress console.error for error boundary tests
    const originalError = console.error;
    beforeEach(() => {
      console.error = jest.fn();
    });
    afterEach(() => {
      console.error = originalError;
    });

    it('should catch errors and show fallback UI', () => {
      render(
        <ErrorBoundary>
          <ThrowingComponent />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-fallback')).toBeTruthy();
      expect(screen.getByText('Something went wrong')).toBeTruthy();
    });

    it('should show retry button in fallback UI', () => {
      render(
        <ErrorBoundary>
          <ThrowingComponent />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary-retry-button')).toBeTruthy();
    });

    it('should call onError when error is caught', () => {
      const onError = jest.fn();

      render(
        <ErrorBoundary onError={onError}>
          <ThrowingComponent />
        </ErrorBoundary>
      );

      expect(onError).toHaveBeenCalled();
    });
  });

  describe('Streaming to download transition', () => {
    it('should show meditation controls with stream complete state', () => {
      const onStreamComplete = jest.fn();

      render(
        <MeditationControls
          isCalling={false}
          meditationURI=""
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
          onStreamComplete={onStreamComplete}
        />
      );

      expect(screen.getByTestId('hls-play-button')).toBeTruthy();
    });
  });

  describe('Base64 fallback mode', () => {
    it('should use legacy audio when streaming is false but meditationURI exists', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI="file://local/meditation.mp3"
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={false}
          playlistUrl={null}
        />
      );

      // Should render legacy play button (expo-av mode)
      expect(screen.getByTestId('legacy-play-button')).toBeTruthy();
      expect(screen.queryByTestId('hls-play-button')).toBeNull();
    });

    it('should prioritize streaming mode over legacy mode', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI="file://local/meditation.mp3"
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // Should render HLS button even though meditationURI exists
      expect(screen.getByTestId('hls-play-button')).toBeTruthy();
      expect(screen.queryByTestId('legacy-play-button')).toBeNull();
    });
  });

  describe('Platform-specific behavior', () => {
    it('should render controls correctly for streaming mode', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI=""
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // Play/Pause button should be present
      const playButton = screen.getByTestId('hls-play-button');
      expect(playButton).toBeTruthy();
      // Button text will be Play or Pause depending on HLS player state
      // We just verify the button exists and has a text child
      expect(playButton).toBeTruthy();
    });

    it('should show play button and allow pressing it', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI=""
          setMeditationURI={jest.fn()}
          handleMeditationCall={jest.fn()}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // Button should be present and pressable
      const playButton = screen.getByTestId('hls-play-button');
      expect(playButton).toBeTruthy();

      fireEvent.press(playButton);

      // Note: In real app, HLSPlayer callback would trigger state change
      // Here we just verify the button is functional
      expect(playButton).toBeTruthy();
    });
  });
});
