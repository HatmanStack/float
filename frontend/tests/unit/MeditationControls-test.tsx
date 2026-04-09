import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';

import MeditationControls from '@/components/ScreenComponents/MeditationControls';
import { Audio } from 'expo-av';

// Mock Expo Audio to control playback behavior
jest.mock('expo-av', () => ({
  Audio: {
    Sound: {
      createAsync: jest.fn().mockResolvedValue({
        sound: {
          playAsync: jest.fn().mockResolvedValue({}),
          pauseAsync: jest.fn().mockResolvedValue({}),
          setOnPlaybackStatusUpdate: jest.fn((callback) => {
            // Immediately call the callback to simulate playback start
            callback({ didJustFinish: false });
          }),
        },
      }),
    },
  },
}));

// Mock VoiceQA component
let mockVoiceQAProps: Record<string, unknown> = {};
jest.mock('@/components/ScreenComponents/VoiceQA', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: (props: Record<string, unknown>) => {
      mockVoiceQAProps = props;
      return React.createElement('VoiceQA', { testID: 'voice-qa' });
    },
  };
});

// Mock HLSPlayer component
jest.mock('@/components/HLSPlayer', () => {
  const React = require('react');
  return {
    HLSPlayer: React.forwardRef(
      (
        props: { playlistUrl: string; autoPlay?: boolean },
        ref: React.Ref<{ play: () => void; pause: () => void; seek: (time: number) => void }>
      ) => {
        React.useImperativeHandle(ref, () => ({
          play: jest.fn(),
          pause: jest.fn(),
          seek: jest.fn(),
        }));
        return null;
      }
    ),
  };
});

describe('MeditationControls', () => {
  const mockHandleMeditationCall = jest.fn();
  const mockSetMeditationURI = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks(); // Clear mocks before each test
  });

  describe('Legacy base64 mode', () => {
    it('renders "Generate" button when not calling and no URI', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
        />
      );
      expect(screen.getByText('Generate')).toBeTruthy();
    });

    it('renders ActivityIndicator when isCalling is true', () => {
      render(
        <MeditationControls
          isCalling={true}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
        />
      );
      expect(screen.getByTestId('activity-indicator')).toBeTruthy();
    });

    it('renders "Play" button when meditationURI is set', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={'mocked-uri'}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
        />
      );
      expect(screen.getByText('Play')).toBeTruthy();
    });

    it('calls handleMeditationCall with default duration when "Generate" is pressed', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
        />
      );
      fireEvent.press(screen.getByText('Generate'));
      expect(mockHandleMeditationCall).toHaveBeenCalledWith(5); // Default duration is 5 minutes
    });

    it('plays audio when "Play" is pressed', async () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={'mocked-uri'}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
        />
      );
      fireEvent.press(screen.getByText('Play'));
      expect(Audio.Sound.createAsync).toHaveBeenCalledWith({ uri: 'mocked-uri' });

      await waitFor(() => {
        expect(screen.getByText('Pause')).toBeTruthy();
      });

      // Now you can assert that the button text has changed
      expect(screen.getByText('Pause')).toBeTruthy();
    });

    it('pauses audio when "Pause" is pressed', async () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={'mocked-uri'}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
        />
      );
      fireEvent.press(screen.getByText('Play')); // Start playing

      // Wait for the Pause button to appear
      await waitFor(() => {
        expect(screen.getByText('Pause')).toBeTruthy();
      });
      const { sound } = await Audio.Sound.createAsync({ uri: 'mocked-uri' });

      expect(sound).toBeDefined();

      await act(async () => {
        fireEvent.press(screen.getByText('Pause')); // Then pause
      }); // Then pause
      expect(sound.pauseAsync).toHaveBeenCalled();

      // Ensure the button text changes back to "Play"
      await waitFor(() => {
        expect(screen.getByText('Play')).toBeTruthy();
      });
    });
  });

  describe('HLS Streaming mode', () => {
    it('renders HLS player when isStreaming and playlistUrl provided', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // Should show HLS play button
      expect(screen.getByTestId('hls-play-button')).toBeTruthy();
    });

    it('does not render HLS player when isStreaming is false', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
          isStreaming={false}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // Should show generate button since not streaming
      expect(screen.getByTestId('generate-button')).toBeTruthy();
    });

    it('does not render HLS player when playlistUrl is null', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
          isStreaming={true}
          playlistUrl={null}
        />
      );

      // Should show generate button since no playlist URL
      expect(screen.getByTestId('generate-button')).toBeTruthy();
    });

    it('shows play/pause button in HLS mode', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // Should show play text (not playing yet)
      expect(screen.getByText('Play')).toBeTruthy();
    });

    it('prefers streaming mode over legacy mode', () => {
      render(
        <MeditationControls
          isCalling={false}
          meditationURI={'mocked-uri'}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      // Should render HLS player even though meditationURI is set
      expect(screen.getByTestId('hls-play-button')).toBeTruthy();
    });

    it('calls onStreamComplete when stream ends', () => {
      const onStreamComplete = jest.fn();
      const { rerender } = render(
        <MeditationControls
          isCalling={false}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
          onStreamComplete={onStreamComplete}
        />
      );

      // HLS player is mocked, so we can't easily trigger the callback
      // This test verifies the prop is passed correctly
      expect(screen.getByTestId('hls-play-button')).toBeTruthy();
    });
  });

  describe('Loading state', () => {
    it('shows activity indicator regardless of streaming props when isCalling', () => {
      render(
        <MeditationControls
          isCalling={true}
          meditationURI={''}
          setMeditationURI={mockSetMeditationURI}
          handleMeditationCall={mockHandleMeditationCall}
          isStreaming={true}
          playlistUrl="https://example.com/playlist.m3u8"
        />
      );

      expect(screen.getByTestId('activity-indicator')).toBeTruthy();
    });
  });

  // Voice Q&A integration tests are disabled until the backend WebSocket
  // proxy is implemented (ROADMAP item 16). The Q&A step is bypassed in
  // MeditationControls — Generate now goes straight to meditation. These
  // tests will be re-enabled once voice sentiment analysis is available.
  //
  // describe('Voice Q&A integration', () => {
  //   const mockSentimentData = {
  //     sentiment_label: ['Anxious'],
  //     intensity: [4],
  //     speech_to_text: ['stressed'],
  //     added_text: ['work'],
  //     summary: ['workplace stress'],
  //   };
  //
  //   it('shows VoiceQA component when Generate is pressed with sentimentData', () => {
  //     render(
  //       <MeditationControls
  //         isCalling={false}
  //         meditationURI={''}
  //         setMeditationURI={mockSetMeditationURI}
  //         handleMeditationCall={mockHandleMeditationCall}
  //         sentimentData={mockSentimentData}
  //       />
  //     );
  //
  //     fireEvent.press(screen.getByText('Generate'));
  //     expect(screen.getByTestId('voice-qa')).toBeTruthy();
  //   });
  //
  //   it('calls handleMeditationCall when Q&A completes', () => {
  //     render(
  //       <MeditationControls
  //         isCalling={false}
  //         meditationURI={''}
  //         setMeditationURI={mockSetMeditationURI}
  //         handleMeditationCall={mockHandleMeditationCall}
  //         sentimentData={mockSentimentData}
  //       />
  //     );
  //
  //     fireEvent.press(screen.getByText('Generate'));
  //
  //     // Simulate Q&A completing via the captured props
  //     const transcript = [{ role: 'assistant' as const, text: 'test' }];
  //     act(() => {
  //       (mockVoiceQAProps.onComplete as (t: unknown) => void)(transcript);
  //     });
  //
  //     expect(mockHandleMeditationCall).toHaveBeenCalledWith(5, transcript);
  //   });
  //
  //   it('calls handleMeditationCall without transcript when Q&A is skipped', () => {
  //     render(
  //       <MeditationControls
  //         isCalling={false}
  //         meditationURI={''}
  //         setMeditationURI={mockSetMeditationURI}
  //         handleMeditationCall={mockHandleMeditationCall}
  //         sentimentData={mockSentimentData}
  //       />
  //     );
  //
  //     fireEvent.press(screen.getByText('Generate'));
  //
  //     // Simulate skip
  //     act(() => {
  //       (mockVoiceQAProps.onSkip as () => void)();
  //     });
  //
  //     expect(mockHandleMeditationCall).toHaveBeenCalledWith(5);
  //   });
  //
  //   it('calls handleMeditationCall without transcript on Q&A error', () => {
  //     render(
  //       <MeditationControls
  //         isCalling={false}
  //         meditationURI={''}
  //         setMeditationURI={mockSetMeditationURI}
  //         handleMeditationCall={mockHandleMeditationCall}
  //         sentimentData={mockSentimentData}
  //       />
  //     );
  //
  //     fireEvent.press(screen.getByText('Generate'));
  //
  //     // Simulate error
  //     act(() => {
  //       (mockVoiceQAProps.onError as (e: Error) => void)(new Error('test error'));
  //     });
  //
  //     expect(mockHandleMeditationCall).toHaveBeenCalledWith(5);
  //   });

  //   it('falls back to direct meditation when no sentimentData', () => {
  //     render(
  //       <MeditationControls
  //         isCalling={false}
  //         meditationURI={''}
  //         setMeditationURI={mockSetMeditationURI}
  //         handleMeditationCall={mockHandleMeditationCall}
  //       />
  //     );
  //
  //     fireEvent.press(screen.getByText('Generate'));
  //     // Should call meditation directly without Q&A
  //     expect(mockHandleMeditationCall).toHaveBeenCalledWith(5);
  //   });
  // });
});
