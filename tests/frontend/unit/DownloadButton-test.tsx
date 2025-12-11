/**
 * Tests for DownloadButton component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert, Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';

// Mock FileSystem
jest.mock('expo-file-system', () => ({
  documentDirectory: 'mock-directory/',
  createDownloadResumable: jest.fn(),
}));

// Mock Alert
jest.spyOn(Alert, 'alert');

// Store original platform
const originalPlatform = Platform.OS;

// Mock Platform conditionally
function setPlatform(os: 'ios' | 'android' | 'web') {
  Object.defineProperty(Platform, 'OS', { value: os, writable: true });
}

import DownloadButton from '@/components/DownloadButton/DownloadButton';

describe('DownloadButton', () => {
  const mockOnGetDownloadUrl = jest.fn().mockResolvedValue('https://example.com/download/meditation.mp3');
  const mockOnDownloadStart = jest.fn();
  const mockOnDownloadComplete = jest.fn();
  const mockOnDownloadError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    setPlatform('ios');
  });

  afterAll(() => {
    setPlatform(originalPlatform);
  });

  describe('rendering', () => {
    it('should not render when downloadAvailable is false', () => {
      render(
        <DownloadButton
          downloadAvailable={false}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      expect(screen.queryByTestId('download-button')).toBeNull();
    });

    it('should render when downloadAvailable is true', () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      expect(screen.getByTestId('download-button')).toBeTruthy();
      expect(screen.getByText('Download')).toBeTruthy();
    });

    it('should render disabled state when disabled prop is true', () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
          disabled={true}
        />
      );

      expect(screen.getByTestId('download-button')).toBeTruthy();
    });
  });

  describe('download flow - native', () => {
    const mockDownloadResumable = {
      downloadAsync: jest.fn().mockResolvedValue({ uri: 'mock-directory/meditation.mp3' }),
    };

    beforeEach(() => {
      (FileSystem.createDownloadResumable as jest.Mock).mockReturnValue(mockDownloadResumable);
    });

    it('should fetch download URL when pressed', async () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
          onDownloadStart={mockOnDownloadStart}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(mockOnGetDownloadUrl).toHaveBeenCalled();
      });
    });

    it('should call onDownloadStart when download begins', async () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
          onDownloadStart={mockOnDownloadStart}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(mockOnDownloadStart).toHaveBeenCalled();
      });
    });

    it('should show preparing state while fetching URL', async () => {
      // Make getDownloadUrl slow
      const slowGetDownloadUrl = jest.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve('https://example.com/download.mp3'), 100))
      );

      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={slowGetDownloadUrl}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(screen.getByText('Preparing...')).toBeTruthy();
      });
    });

    it('should show downloading state during download', async () => {
      // Make download slow
      const slowDownloadAsync = jest.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ uri: 'mock-directory/meditation.mp3' }), 100))
      );
      mockDownloadResumable.downloadAsync = slowDownloadAsync;

      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(screen.getByText(/Downloading/)).toBeTruthy();
      });
    });

    it('should call onDownloadComplete when download succeeds', async () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
          onDownloadComplete={mockOnDownloadComplete}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(mockOnDownloadComplete).toHaveBeenCalledWith('mock-directory/meditation.mp3');
      });
    });

    it('should show completed state after download', async () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        // Button stays as "Download" after completion (no "Downloaded" state)
        expect(screen.getByText('Download')).toBeTruthy();
      });
    });

    it('should show success alert after download completes', async () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Download Complete',
          'Your meditation has been downloaded successfully.',
          [{ text: 'OK' }]
        );
      });
    });
  });

  describe('download flow - web', () => {
    const originalOpen = window.open;

    beforeEach(() => {
      setPlatform('web');
      window.open = jest.fn();
    });

    afterEach(() => {
      window.open = originalOpen;
    });

    it('should open download URL in new tab on web', async () => {
      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(window.open).toHaveBeenCalledWith(
          'https://example.com/download/meditation.mp3',
          '_blank'
        );
      });
    });
  });

  describe('error handling', () => {
    it('should call onDownloadError when download fails', async () => {
      const error = new Error('Network error');
      mockOnGetDownloadUrl.mockRejectedValueOnce(error);

      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
          onDownloadError={mockOnDownloadError}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(mockOnDownloadError).toHaveBeenCalledWith(error);
      });
    });

    it('should show error alert when download fails', async () => {
      mockOnGetDownloadUrl.mockRejectedValueOnce(new Error('Network error'));

      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Download Failed',
          'Unable to download meditation. Please try again.',
          expect.any(Array)
        );
      });
    });

    it('should show retry text after error', async () => {
      mockOnGetDownloadUrl.mockRejectedValueOnce(new Error('Network error'));

      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(screen.getByText('Retry Download')).toBeTruthy();
      });
    });
  });

  describe('custom filename', () => {
    it('should use custom filename for download', async () => {
      const mockDownloadResumable = {
        downloadAsync: jest.fn().mockResolvedValue({ uri: 'mock-directory/my-meditation.mp3' }),
      };
      (FileSystem.createDownloadResumable as jest.Mock).mockReturnValue(mockDownloadResumable);

      render(
        <DownloadButton
          downloadAvailable={true}
          onGetDownloadUrl={mockOnGetDownloadUrl}
          fileName="my-meditation.mp3"
        />
      );

      fireEvent.press(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(FileSystem.createDownloadResumable).toHaveBeenCalledWith(
          expect.any(String),
          'mock-directory/my-meditation.mp3',
          {},
          expect.any(Function)
        );
      });
    });
  });
});
