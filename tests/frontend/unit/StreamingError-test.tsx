/**
 * Tests for StreamingError component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';

import StreamingError, { getErrorMessage } from '@/components/StreamingError';

describe('StreamingError', () => {
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render error message', () => {
      const error = new Error('Test error');

      render(<StreamingError error={error} onRetry={mockOnRetry} />);

      expect(screen.getByTestId('streaming-error')).toBeTruthy();
      expect(screen.getByTestId('streaming-error-message')).toBeTruthy();
    });

    it('should render retry button when canRetry is true', () => {
      const error = new Error('Test error');

      render(<StreamingError error={error} onRetry={mockOnRetry} canRetry={true} />);

      expect(screen.getByTestId('streaming-error-retry-button')).toBeTruthy();
    });

    it('should not render retry button when canRetry is false', () => {
      const error = new Error('Test error');

      render(<StreamingError error={error} onRetry={mockOnRetry} canRetry={false} />);

      expect(screen.queryByTestId('streaming-error-retry-button')).toBeNull();
    });

    it('should render retry button by default', () => {
      const error = new Error('Test error');

      render(<StreamingError error={error} onRetry={mockOnRetry} />);

      expect(screen.getByTestId('streaming-error-retry-button')).toBeTruthy();
    });
  });

  describe('retry functionality', () => {
    it('should call onRetry when retry button is pressed', () => {
      const error = new Error('Test error');

      render(<StreamingError error={error} onRetry={mockOnRetry} />);

      fireEvent.press(screen.getByTestId('streaming-error-retry-button'));

      expect(mockOnRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('getErrorMessage', () => {
    it('should return network error message for network errors', () => {
      const networkError = new Error('Network request failed');
      expect(getErrorMessage(networkError)).toBe('Connection lost. Check your internet and try again.');
    });

    it('should return network error message for fetch errors', () => {
      const fetchError = new Error('Fetch error occurred');
      expect(getErrorMessage(fetchError)).toBe('Connection lost. Check your internet and try again.');
    });

    it('should return network error message for connection errors', () => {
      const connectionError = new Error('Connection refused');
      expect(getErrorMessage(connectionError)).toBe('Connection lost. Check your internet and try again.');
    });

    it('should return playback error message for HLS errors', () => {
      const hlsError = new Error('HLS fatal error: manifestLoadError');
      expect(getErrorMessage(hlsError)).toBe('Playback failed. Tap retry to start over.');
    });

    it('should return playback error message for manifest errors', () => {
      const manifestError = new Error('Failed to load manifest');
      expect(getErrorMessage(manifestError)).toBe('Playback failed. Tap retry to start over.');
    });

    it('should return playback error message for playlist errors', () => {
      const playlistError = new Error('Playlist parsing failed');
      expect(getErrorMessage(playlistError)).toBe('Playback failed. Tap retry to start over.');
    });

    it('should return generation error message for generation failures', () => {
      const generationError = new Error('Generation failed after 3 attempts');
      expect(getErrorMessage(generationError)).toBe('Could not generate meditation. Please try again.');
    });

    it('should return generation error message for timeout errors', () => {
      const timeoutError = new Error('Request timeout');
      expect(getErrorMessage(timeoutError)).toBe('Could not generate meditation. Please try again.');
    });

    it('should return download error message for download failures', () => {
      const downloadError = new Error('Download interrupted');
      expect(getErrorMessage(downloadError)).toBe('Download failed. Tap to retry.');
    });

    it('should return default message for unknown errors', () => {
      const unknownError = new Error('Something unexpected happened');
      expect(getErrorMessage(unknownError)).toBe('Something went wrong. Please try again.');
    });
  });
});
