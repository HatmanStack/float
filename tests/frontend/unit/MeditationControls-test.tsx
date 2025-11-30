import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';

import MeditationControls from '../../frontend/components/ScreenComponents/MeditationControls';
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

describe('MeditationControls', () => {
  const mockHandleMeditationCall = jest.fn();
  const mockSetMeditationURI = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks(); // Clear mocks before each test
  });

  it('renders "Generate Meditation" button when not calling and no URI', () => {
    render(
      <MeditationControls
        isCalling={false}
        meditationURI={''}
        setMeditationURI={mockSetMeditationURI}
        handleMeditationCall={mockHandleMeditationCall}
      />
    );
    expect(screen.getByText('Generate Meditation')).toBeTruthy();
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

  it('calls handleMeditationCall when "Generate Meditation" is pressed', () => {
    render(
      <MeditationControls
        isCalling={false}
        meditationURI={''}
        setMeditationURI={mockSetMeditationURI}
        handleMeditationCall={mockHandleMeditationCall}
      />
    );
    fireEvent.press(screen.getByText('Generate Meditation'));
    expect(mockHandleMeditationCall).toHaveBeenCalled();
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

  // Add more tests for other scenarios and edge cases as needed
});
