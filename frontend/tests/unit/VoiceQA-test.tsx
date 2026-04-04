import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';
import type { QATranscript, QAState, QAExchange } from '@/types/api';

// Mock useGeminiLiveAPI hook
const mockStartSession = jest.fn().mockResolvedValue(undefined);
const mockEndSession = jest.fn();
const mockSendAudioChunk = jest.fn();
const mockSendTextMessage = jest.fn();

let mockHookReturn: {
  state: QAState;
  transcript: QAExchange[];
  startSession: jest.Mock;
  endSession: jest.Mock;
  sendAudioChunk: jest.Mock;
  sendTextMessage: jest.Mock;
} = {
  state: 'idle',
  transcript: [],
  startSession: mockStartSession,
  endSession: mockEndSession,
  sendAudioChunk: mockSendAudioChunk,
  sendTextMessage: mockSendTextMessage,
};

jest.mock('@/hooks/useGeminiLiveAPI', () => ({
  __esModule: true,
  default: jest.fn(() => mockHookReturn),
}));

// Mock expo-av Audio
const mockRequestPermissionsAsync = jest.fn().mockResolvedValue({ granted: true });
jest.mock('expo-av', () => {
  return {
    __esModule: true,
    Audio: {
      requestPermissionsAsync: (...args: unknown[]) => mockRequestPermissionsAsync(...args),
      Recording: jest.fn(),
      RecordingOptionsPresets: {
        HIGH_QUALITY: {},
      },
    },
  };
});

// Mock MaterialIcons
jest.mock('@expo/vector-icons/MaterialIcons', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: (props: { name: string; testID?: string }) =>
      React.createElement('MaterialIcons', props),
  };
});

import VoiceQA from '@/components/ScreenComponents/VoiceQA';
import type { TransformedDict } from '@/components/BackendMeditationCall';

const mockSentimentData: TransformedDict = {
  sentiment_label: ['Anxious'],
  intensity: [4],
  speech_to_text: ['I had a stressful day'],
  added_text: ['Work was overwhelming'],
  summary: ['Workplace stress'],
};

describe('VoiceQA', () => {
  const mockOnComplete = jest.fn();
  const mockOnSkip = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockHookReturn = {
      state: 'idle',
      transcript: [],
      startSession: mockStartSession,
      endSession: mockEndSession,
      sendAudioChunk: mockSendAudioChunk,
      sendTextMessage: mockSendTextMessage,
    };
    mockRequestPermissionsAsync.mockResolvedValue({ granted: true });
  });

  const renderVoiceQA = () =>
    render(
      <VoiceQA
        sentimentData={mockSentimentData}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
        onError={mockOnError}
      />
    );

  it('renders connecting state', () => {
    mockHookReturn = { ...mockHookReturn, state: 'connecting' };
    renderVoiceQA();
    expect(screen.getByText(/connecting/i)).toBeTruthy();
  });

  it('renders listening state with mic icon', () => {
    mockHookReturn = { ...mockHookReturn, state: 'listening' };
    renderVoiceQA();
    expect(screen.getByText(/listening/i)).toBeTruthy();
  });

  it('renders transcript exchanges', () => {
    mockHookReturn = {
      ...mockHookReturn,
      state: 'listening',
      transcript: [
        { role: 'assistant', text: 'How are you feeling?' },
        { role: 'user', text: 'I feel stressed' },
      ],
    };
    renderVoiceQA();
    expect(screen.getByText('How are you feeling?')).toBeTruthy();
    expect(screen.getByText('I feel stressed')).toBeTruthy();
  });

  it('skip button calls onSkip', () => {
    mockHookReturn = { ...mockHookReturn, state: 'listening' };
    renderVoiceQA();
    const skipButton = screen.getByText(/skip/i);
    fireEvent.press(skipButton);
    expect(mockOnSkip).toHaveBeenCalled();
  });

  it('calls onComplete when session completes', async () => {
    const transcript: QATranscript = [
      { role: 'assistant', text: 'How are you feeling?' },
      { role: 'user', text: 'Stressed' },
    ];
    mockHookReturn = { ...mockHookReturn, state: 'complete', transcript };
    renderVoiceQA();

    await waitFor(() => {
      expect(mockOnComplete).toHaveBeenCalledWith(transcript);
    });
  });

  it('requests microphone permission on mount', async () => {
    renderVoiceQA();
    await waitFor(() => {
      expect(mockRequestPermissionsAsync).toHaveBeenCalled();
    });
  });

  // Text fallback tests (Task 3)
  it('shows text input when mic permission is denied', async () => {
    mockRequestPermissionsAsync.mockResolvedValue({ granted: false });
    mockHookReturn = { ...mockHookReturn, state: 'listening' };
    renderVoiceQA();

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type your response/i)).toBeTruthy();
    });
  });

  it('sends text message via send button in text mode', async () => {
    mockRequestPermissionsAsync.mockResolvedValue({ granted: false });
    mockHookReturn = { ...mockHookReturn, state: 'listening' };
    renderVoiceQA();

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type your response/i)).toBeTruthy();
    });

    const input = screen.getByPlaceholderText(/type your response/i);
    fireEvent.changeText(input, 'I feel overwhelmed');
    fireEvent.press(screen.getByText(/send/i));

    expect(mockSendTextMessage).toHaveBeenCalledWith('I feel overwhelmed');
  });

  it('shows mic not available message in text mode', async () => {
    mockRequestPermissionsAsync.mockResolvedValue({ granted: false });
    mockHookReturn = { ...mockHookReturn, state: 'listening' };
    renderVoiceQA();

    await waitFor(() => {
      expect(screen.getByText(/microphone not available/i)).toBeTruthy();
    });
  });

  it('shows transcript correctly in text mode', async () => {
    mockRequestPermissionsAsync.mockResolvedValue({ granted: false });
    mockHookReturn = {
      ...mockHookReturn,
      state: 'listening',
      transcript: [
        { role: 'assistant', text: 'Tell me more.' },
        { role: 'user', text: 'Work was tough.' },
      ],
    };
    renderVoiceQA();

    await waitFor(() => {
      expect(screen.getByText('Tell me more.')).toBeTruthy();
      expect(screen.getByText('Work was tough.')).toBeTruthy();
    });
  });
});
