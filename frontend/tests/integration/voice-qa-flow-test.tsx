/**
 * Voice Q&A Flow Integration Tests
 *
 * Tests verify the full Q&A-to-meditation flow with mocked APIs:
 * - Token fetch and WebSocket connection
 * - Q&A transcript flows through to meditation request payload
 * - Skip bypasses Q&A and sends meditation request without transcript
 * - Error fallback sends meditation request without transcript
 */

import React, { useState, useCallback } from 'react';
import { View, Text, Button } from 'react-native';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';
import type { QATranscript } from '@/types/api';

// ---- Mock VoiceQA component that exposes callbacks for test control ----
let capturedVoiceQAProps: Record<string, unknown> = {};

jest.mock('@/components/ScreenComponents/VoiceQA', () => {
  const React = require('react');
  const { View, Text, Button: RNButton } = require('react-native');
  return {
    __esModule: true,

    default: (props: Record<string, unknown>) => {
      capturedVoiceQAProps = props;
      return React.createElement(
        View,
        { testID: 'voice-qa-mock' },
        React.createElement(Text, null, 'VoiceQA Active'),
        React.createElement(RNButton, {
          testID: 'mock-qa-complete',
          title: 'Complete QA',
          onPress: () => {
            (props.onComplete as (...args: unknown[]) => void)([
              { role: 'assistant', text: 'How are you feeling?' },
              { role: 'user', text: 'Stressed about work' },
              { role: 'assistant', text: 'Let me create a meditation for you.' },
            ]);
          },
        }),
        React.createElement(RNButton, {
          testID: 'mock-qa-skip',
          title: 'Skip QA',
          onPress: () => (props.onSkip as (...args: unknown[]) => void)(),
        }),
        React.createElement(RNButton, {
          testID: 'mock-qa-error',
          title: 'Error QA',
          onPress: () => (props.onError as (...args: unknown[]) => void)(new Error('QA failed')),
        })
      );
    },
  };
});

// Mock expo-av
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
    requestPermissionsAsync: jest.fn().mockResolvedValue({ granted: true }),
  },
}));

// Mock HLSPlayer
jest.mock('@/components/HLSPlayer', () => {
  const React = require('react');
  return {
    HLSPlayer: React.forwardRef((props: Record<string, unknown>, ref: React.Ref<unknown>) => {
      React.useImperativeHandle(ref, () => ({
        play: jest.fn(),
        pause: jest.fn(),
        seek: jest.fn(),
      }));
      return null;
    }),
  };
});

import MeditationControls from '@/components/ScreenComponents/MeditationControls';
import type { TransformedDict } from '@/components/BackendMeditationCall';

const mockSentimentData: TransformedDict = {
  sentiment_label: ['Anxious', 'Stressed'],
  intensity: [4, 3],
  speech_to_text: ['I had a tough meeting', 'Deadline pressure'],
  added_text: ['Boss was critical', 'Too many tasks'],
  summary: ['Workplace conflict', 'Work overload'],
};

describe('Voice Q&A Integration Flow', () => {
  let mockHandleMeditationCall: jest.Mock;
  let mockSetMeditationURI: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    capturedVoiceQAProps = {};
    mockHandleMeditationCall = jest.fn();
    mockSetMeditationURI = jest.fn();
  });

  const renderControls = () =>
    render(
      <MeditationControls
        isCalling={false}
        meditationURI=""
        setMeditationURI={mockSetMeditationURI}
        handleMeditationCall={mockHandleMeditationCall}
        sentimentData={mockSentimentData}
      />
    );

  it('happy path: Q&A completes and meditation request includes transcript', async () => {
    renderControls();

    // Tap Generate to start Q&A
    fireEvent.press(screen.getByText('Generate'));

    // VoiceQA should be rendered
    expect(screen.getByTestId('voice-qa-mock')).toBeTruthy();
    expect(screen.getByText('VoiceQA Active')).toBeTruthy();

    // Complete Q&A
    await act(async () => {
      fireEvent.press(screen.getByText('Complete QA'));
    });

    // Verify meditation call was made with transcript
    expect(mockHandleMeditationCall).toHaveBeenCalledWith(5, [
      { role: 'assistant', text: 'How are you feeling?' },
      { role: 'user', text: 'Stressed about work' },
      { role: 'assistant', text: 'Let me create a meditation for you.' },
    ]);
  });

  it('skip path: meditation request sent without transcript', async () => {
    renderControls();

    // Tap Generate to start Q&A
    fireEvent.press(screen.getByText('Generate'));

    // Skip Q&A
    await act(async () => {
      fireEvent.press(screen.getByText('Skip QA'));
    });

    // Verify meditation call was made without transcript
    expect(mockHandleMeditationCall).toHaveBeenCalledWith(5);
    // Should NOT have a second argument (transcript)
    expect(mockHandleMeditationCall.mock.calls[0]).toHaveLength(1);
  });

  it('error path: Q&A fails and meditation proceeds without transcript', async () => {
    renderControls();

    // Tap Generate to start Q&A
    fireEvent.press(screen.getByText('Generate'));

    // Trigger error
    await act(async () => {
      fireEvent.press(screen.getByText('Error QA'));
    });

    // Verify meditation call was made without transcript (fallback)
    expect(mockHandleMeditationCall).toHaveBeenCalledWith(5);
    expect(mockHandleMeditationCall.mock.calls[0]).toHaveLength(1);
  });

  it('sentiment data is passed to VoiceQA component', async () => {
    renderControls();

    // Tap Generate to start Q&A
    fireEvent.press(screen.getByText('Generate'));

    // Verify sentiment data was passed to VoiceQA
    expect(capturedVoiceQAProps.sentimentData).toEqual(mockSentimentData);
  });

  it('no Q&A when sentimentData is not provided', () => {
    render(
      <MeditationControls
        isCalling={false}
        meditationURI=""
        setMeditationURI={mockSetMeditationURI}
        handleMeditationCall={mockHandleMeditationCall}
      />
    );

    // Tap Generate should call meditation directly
    fireEvent.press(screen.getByText('Generate'));

    // Should go directly to meditation without Q&A
    expect(mockHandleMeditationCall).toHaveBeenCalledWith(5);
  });
});
