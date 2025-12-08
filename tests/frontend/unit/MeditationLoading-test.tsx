/**
 * Tests for MeditationLoading component
 */

import React from 'react';
import { render, screen } from '@testing-library/react-native';

import MeditationLoading, { getLoadingMessage } from '@/components/ScreenComponents/MeditationLoading';

describe('MeditationLoading', () => {
  describe('rendering', () => {
    it('should render loading indicator', () => {
      render(<MeditationLoading state="starting" />);

      expect(screen.getByTestId('meditation-loading')).toBeTruthy();
      expect(screen.getByTestId('meditation-loading-indicator')).toBeTruthy();
    });

    it('should render loading message', () => {
      render(<MeditationLoading state="starting" />);

      expect(screen.getByTestId('meditation-loading-message')).toBeTruthy();
    });
  });

  describe('loading states', () => {
    it('should show "Starting meditation..." for starting state', () => {
      render(<MeditationLoading state="starting" />);

      expect(screen.getByText('Starting meditation...')).toBeTruthy();
    });

    it('should show "Preparing audio..." for preparing state', () => {
      render(<MeditationLoading state="preparing" />);

      expect(screen.getByText('Preparing audio...')).toBeTruthy();
    });

    it('should show "Ready to play" for ready state', () => {
      render(<MeditationLoading state="ready" />);

      expect(screen.getByText('Ready to play')).toBeTruthy();
    });

    it('should show "Streaming..." for streaming state', () => {
      render(<MeditationLoading state="streaming" />);

      expect(screen.getByText('Streaming...')).toBeTruthy();
    });
  });

  describe('progress display', () => {
    it('should show progress when streaming with segments', () => {
      render(
        <MeditationLoading
          state="streaming"
          segmentsCompleted={5}
          segmentsTotal={36}
        />
      );

      expect(screen.getByTestId('meditation-loading-progress')).toBeTruthy();
      expect(screen.getByText('5/36 segments')).toBeTruthy();
    });

    it('should show indeterminate progress when total unknown', () => {
      render(
        <MeditationLoading
          state="streaming"
          segmentsCompleted={5}
          segmentsTotal={null}
        />
      );

      expect(screen.getByTestId('meditation-loading-progress')).toBeTruthy();
      expect(screen.getByText('5 segments loaded')).toBeTruthy();
    });

    it('should not show progress when not streaming', () => {
      render(<MeditationLoading state="preparing" segmentsCompleted={5} />);

      expect(screen.queryByTestId('meditation-loading-progress')).toBeNull();
    });

    it('should not show progress when segments undefined', () => {
      render(<MeditationLoading state="streaming" />);

      expect(screen.queryByTestId('meditation-loading-progress')).toBeNull();
    });
  });

  describe('getLoadingMessage', () => {
    it('should return correct message for starting state', () => {
      expect(getLoadingMessage('starting')).toBe('Starting meditation...');
    });

    it('should return correct message for preparing state', () => {
      expect(getLoadingMessage('preparing')).toBe('Preparing audio...');
    });

    it('should return correct message for ready state', () => {
      expect(getLoadingMessage('ready')).toBe('Ready to play');
    });

    it('should return correct message for streaming state', () => {
      expect(getLoadingMessage('streaming')).toBe('Streaming...');
    });
  });
});
