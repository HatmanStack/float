import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';

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

  it('renders initial check-in prompt', () => {
    renderVoiceQA();
    expect(screen.getByText('Quick check-in')).toBeTruthy();
    expect(screen.getByText(/how are you feeling/i)).toBeTruthy();
  });

  it('renders text input', () => {
    renderVoiceQA();
    expect(screen.getByPlaceholderText(/type your response/i)).toBeTruthy();
  });

  it('renders skip button', () => {
    renderVoiceQA();
    expect(screen.getByText(/skip check-in/i)).toBeTruthy();
  });

  it('skip button calls onSkip', () => {
    renderVoiceQA();
    fireEvent.press(screen.getByText(/skip check-in/i));
    expect(mockOnSkip).toHaveBeenCalled();
  });

  it('sends text and shows next prompt', () => {
    renderVoiceQA();
    const input = screen.getByPlaceholderText(/type your response/i);
    fireEvent.changeText(input, 'I feel stressed');
    fireEvent(input, 'submitEditing');

    // User response should appear
    expect(screen.getByText('I feel stressed')).toBeTruthy();
    // Next prompt should appear
    expect(screen.getByText(/anything specific weighing/i)).toBeTruthy();
  });

  it('calls onComplete after max exchanges', () => {
    renderVoiceQA();
    const input = screen.getByPlaceholderText(/type your response/i);

    // Exchange 1
    fireEvent.changeText(input, 'Stressed about work');
    fireEvent(input, 'submitEditing');

    // Exchange 2
    fireEvent.changeText(input, 'My boss was difficult');
    fireEvent(input, 'submitEditing');

    // Exchange 3 — triggers completion
    fireEvent.changeText(input, 'Just need to relax');
    fireEvent(input, 'submitEditing');

    expect(mockOnComplete).toHaveBeenCalledTimes(1);
    const transcript = mockOnComplete.mock.calls[0][0];
    expect(transcript.length).toBeGreaterThan(0);
    // Should contain user responses
    expect(transcript.some((e: { text: string }) => e.text === 'Stressed about work')).toBe(true);
  });

  it('does not send empty text', () => {
    renderVoiceQA();
    const input = screen.getByPlaceholderText(/type your response/i);
    fireEvent.changeText(input, '   ');
    fireEvent(input, 'submitEditing');

    // Should still only have the initial prompt, no user exchange
    expect(screen.queryByText('You')).toBeNull();
  });

  it('shows Guide and You labels in transcript', () => {
    renderVoiceQA();
    // Initial prompt has Guide label
    expect(screen.getByText('Guide')).toBeTruthy();

    const input = screen.getByPlaceholderText(/type your response/i);
    fireEvent.changeText(input, 'Feeling anxious');
    fireEvent(input, 'submitEditing');

    expect(screen.getAllByText('Guide').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('You')).toBeTruthy();
  });
});
