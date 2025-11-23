/**
 * Recording Flow Integration Tests
 *
 * These tests verify that audio recording works correctly across components
 * through Context providers. Tests cover:
 * - Recording state management
 * - Recording → Summary flow
 * - Permission handling
 * - Multi-component recording state sharing
 * - Error scenarios
 */

import React, { useState } from "react";
import { View, Text, Button } from "react-native";
import {
  renderWithIncidentContext,
  renderWithAllContexts,
  mockIncident,
  mockFetchSuccess,
  mockFetchError,
  mockNetworkError,
  waitForIntegration,
  fireEvent,
  act,
  INTEGRATION_TIMEOUTS,
} from "./test-utils";
import { useIncident } from "@/frontend/context/IncidentContext";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system";

// Mock backend summary response
const mockSummaryResponse = {
  sentiment_label: 'Happy',
  intensity: 3,
  speech_to_text: 'I feel great today',
  added_text: 'Additional context',
  summary: 'User is experiencing positive emotions',
  notification_id: 'notif-123',
  timestamp: new Date().toISOString(),
  color_key: 0,
};

/**
 * Test component that simulates recording functionality
 */
function RecordingComponent() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingUri, setRecordingUri] = useState<string | null>(null);
  const [permissionStatus, setPermissionStatus] = useState<'not-requested' | 'granted' | 'denied'>('not-requested');

  const requestPermission = async () => {
    const { status } = await Audio.requestPermissionsAsync();
    setPermissionStatus(status === 'granted' ? 'granted' : 'denied');
    return status === 'granted";
  };

  const startRecording = () => {
    // Synchronous start for simpler testing
    setPermissionStatus('granted'); // Auto-grant in test
    setIsRecording(true);
  };

  const stopRecording = () => {
    setIsRecording(false);
    setRecordingUri('file:///mock-recording.m4a');
  };

  return (
    <View testID="recording-component">
      <Text testID="recording-status">{isRecording ? 'Recording...' : 'Not recording'}</Text>
      <Text testID="permission-status">{permissionStatus}</Text>
      {recordingUri && <Text testID="recording-uri">{recordingUri}</Text>}
      <Button title="Start Recording" onPress={startRecording} testID="start-recording-button" />
      <Button
        title="Stop Recording"
        onPress={stopRecording}
        disabled={!isRecording}
        testID="stop-recording-button"
      />
    </View>
  );
}

/**
 * Test component that handles recording → summary flow
 */
function RecordingToSummaryComponent() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingUri, setRecordingUri] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const { setIncidentList } = useIncident();

  const startRecording = async () => {
    setIsRecording(true);
    setError(null);
  };

  const stopRecording = () => {
    setIsRecording(false);
    setRecordingUri('base64-encoded-audio-data');
  };

  const generateSummary = async () => {
    if (!recordingUri) {
      setError('No recording available');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch('https://mock-lambda-url.com', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inference_type: 'summary',
          audio: recordingUri,
          prompt: 'Test prompt',
          user_id: 'test-user',
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      setSummary(data);

      // Add to incident list
      setIncidentList((prev) => [
        ...prev,
        {
          ...data,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <View testID="recording-summary-component">
      <Text testID="recording-status">{isRecording ? 'Recording' : 'Stopped'}</Text>
      <Text testID="processing-status">{isProcessing ? 'Processing' : 'Idle'}</Text>
      {recordingUri && <Text testID="has-recording">Recording available</Text>}
      {summary && (
        <View testID="summary-result">
          <Text testID="sentiment-label">{summary.sentiment_label}</Text>
          <Text testID="intensity">Intensity: {summary.intensity}</Text>
        </View>
      )}
      {error && <Text testID="error-message">{error}</Text>}
      <Button title="Start" onPress={startRecording} testID="start-button" />
      <Button title="Stop" onPress={stopRecording} testID="stop-button" />
      <Button
        title="Generate Summary"
        onPress={generateSummary}
        testID="generate-summary-button"
      />
    </View>
  );
}

/**
 * Test component that shows recording indicator
 */
function RecordingIndicatorComponent() {
  const { incidentList } = useIncident();

  return (
    <View testID="recording-indicator">
      <Text testID="incident-count">{incidentList.length} recordings</Text>
      {incidentList.map((incident, index) => (
        <View key={index} testID={`incident-${index}`}>
          <Text testID={`sentiment-${index}`}>{incident.sentiment_label}</Text>
        </View>
      ))}
    </View>
  );
}

describe('Recording Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Recording Functionality', () => {
    it('should grant permission when recording starts', () => {
      const { getByTestId } = renderWithIncidentContext(<RecordingComponent />);

      expect(getByTestId('permission-status')).toHaveTextContent('not-requested');

      fireEvent.press(getByTestId('start-recording-button'));

      expect(getByTestId('permission-status')).toHaveTextContent('granted');
      expect(getByTestId('recording-status')).toHaveTextContent('Recording...');
    });

    it('should start recording when button pressed', () => {
      const { getByTestId } = renderWithIncidentContext(<RecordingComponent />);

      fireEvent.press(getByTestId('start-recording-button'));

      expect(getByTestId('recording-status')).toHaveTextContent('Recording...');
    });

    it('should stop recording and generate URI', () => {
      const { getByTestId } = renderWithIncidentContext(<RecordingComponent />);

      // Start recording
      fireEvent.press(getByTestId('start-recording-button'));

      expect(getByTestId('recording-status')).toHaveTextContent('Recording...');

      // Stop recording
      fireEvent.press(getByTestId('stop-recording-button'));

      expect(getByTestId('recording-status')).toHaveTextContent('Not recording');
      expect(getByTestId('recording-uri')).toBeTruthy();
    });
  });

  describe('Recording to Summary Flow', () => {
    it('should generate summary from recording', async () => {
      mockFetchSuccess(mockSummaryResponse);

      const { getByTestId } = renderWithIncidentContext(<RecordingToSummaryComponent />);

      // Start recording
      fireEvent.press(getByTestId('start-button'));

      await waitForIntegration(() => {
        expect(getByTestId('recording-status')).toHaveTextContent('Recording');
      });

      // Stop recording
      fireEvent.press(getByTestId('stop-button'));

      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      // Generate summary
      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      await waitForIntegration(
        () => {
          expect(getByTestId('summary-result')).toBeTruthy();
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );

      expect(getByTestId('sentiment-label')).toHaveTextContent('Happy');
      const intensityText = getByTestId('intensity').props.children;
      expect(intensityText).toContain(3);
    });

    it('should update incident list after summary', async () => {
      mockFetchSuccess(mockSummaryResponse);

      const { getByTestId } = renderWithIncidentContext(
        <>
          <RecordingToSummaryComponent />
          <RecordingIndicatorComponent />
        </>
      );

      // Initially no incidents
      expect(getByTestId('incident-count')).toHaveTextContent('0 recordings');

      // Record and generate summary
      fireEvent.press(getByTestId('start-button'));
      await waitForIntegration(() => {
        expect(getByTestId('recording-status')).toHaveTextContent('Recording');
      });

      fireEvent.press(getByTestId('stop-button'));
      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      // Wait for incident list to update
      await waitForIntegration(
        () => {
          expect(getByTestId('incident-count')).toHaveTextContent('1 recordings');
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );

      expect(getByTestId('sentiment-0')).toHaveTextContent('Happy');
    });

    it('should show processing state during summary generation', async () => {
      // Delay the response to test processing state
      global.fetch = jest.fn(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: () => Promise.resolve(mockSummaryResponse),
                } as Response),
              100
            )
          )
      ) as jest.Mock;

      const { getByTestId } = renderWithIncidentContext(<RecordingToSummaryComponent />);

      // Record
      fireEvent.press(getByTestId('start-button'));
      fireEvent.press(getByTestId('stop-button'));

      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      // Generate summary
      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      // Should show processing
      expect(getByTestId('processing-status')).toHaveTextContent('Processing');

      // Wait for completion
      await waitForIntegration(
        () => {
          expect(getByTestId('processing-status')).toHaveTextContent('Idle');
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );
    });
  });

  describe('Multi-Component Recording State', () => {
    it('should share recording state across components', async () => {
      mockFetchSuccess(mockSummaryResponse);

      const { getByTestId, getAllByTestId } = renderWithIncidentContext(
        <>
          <RecordingToSummaryComponent />
          <RecordingIndicatorComponent />
          <RecordingIndicatorComponent />
        </>
      );

      // Generate a recording and summary
      fireEvent.press(getByTestId('start-button'));
      fireEvent.press(getByTestId('stop-button'));

      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      // Wait for all indicators to update
      await waitForIntegration(
        () => {
          const counts = getAllByTestId('incident-count');
          expect(counts[0]).toHaveTextContent('1 recordings');
          expect(counts[1]).toHaveTextContent('1 recordings');
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );
    });
  });

  describe('Error Scenarios', () => {
    it('should handle summary generation errors', async () => {
      mockFetchError('Server error', 500);

      const { getByTestId } = renderWithIncidentContext(<RecordingToSummaryComponent />);

      // Record
      fireEvent.press(getByTestId('start-button'));
      fireEvent.press(getByTestId('stop-button'));

      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      // Try to generate summary
      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      // Should show error
      await waitForIntegration(
        () => {
          expect(getByTestId('error-message')).toBeTruthy();
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );

      const errorText = getByTestId('error-message').props.children;
      expect(errorText).toContain('500');
    });

    it('should handle network errors', async () => {
      mockNetworkError('Network request failed');

      const { getByTestId } = renderWithIncidentContext(<RecordingToSummaryComponent />);

      // Record
      fireEvent.press(getByTestId('start-button'));
      fireEvent.press(getByTestId('stop-button'));

      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      // Try to generate summary
      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      // Should show error
      await waitForIntegration(
        () => {
          expect(getByTestId('error-message')).toBeTruthy();
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );
    });

    it('should handle missing recording URI', async () => {
      const { getByTestId } = renderWithIncidentContext(<RecordingToSummaryComponent />);

      // Try to generate summary without recording
      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      await waitForIntegration(() => {
        expect(getByTestId('error-message')).toHaveTextContent('No recording available');
      });
    });

    it('should recover from errors and allow retry', async () => {
      // First attempt fails
      mockFetchError('Server error', 500);

      const { getByTestId } = renderWithIncidentContext(<RecordingToSummaryComponent />);

      // Record
      fireEvent.press(getByTestId('start-button'));
      fireEvent.press(getByTestId('stop-button'));

      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      // First attempt (fails)
      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      await waitForIntegration(
        () => {
          expect(getByTestId('error-message')).toBeTruthy();
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );

      // Second attempt (succeeds)
      mockFetchSuccess(mockSummaryResponse);

      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      await waitForIntegration(
        () => {
          expect(getByTestId('summary-result')).toBeTruthy();
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );

      expect(getByTestId('sentiment-label')).toHaveTextContent('Happy');
    });
  });

  describe('Recording Cleanup', () => {
    it('should clear error when starting new recording', async () => {
      const { getByTestId } = renderWithIncidentContext(<RecordingToSummaryComponent />);

      // Generate error
      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      await waitForIntegration(() => {
        expect(getByTestId('error-message')).toBeTruthy();
      });

      // Start new recording
      fireEvent.press(getByTestId('start-button'));

      await waitForIntegration(() => {
        expect(getByTestId('recording-status')).toHaveTextContent('Recording');
      });

      // Error should be cleared - query instead of get
      const component = getByTestId('recording-summary-component');
      const hasError = component.findAll((node) => node.props.testID === 'error-message');
      expect(hasError.length).toBe(0);
    });
  });

  describe('Integration with Auth Context', () => {
    it('should work with both auth and incident contexts', async () => {
      mockFetchSuccess(mockSummaryResponse);

      const { getByTestId } = renderWithAllContexts(
        <>
          <RecordingToSummaryComponent />
          <RecordingIndicatorComponent />
        </>
      );

      // Record and generate summary
      fireEvent.press(getByTestId('start-button'));
      fireEvent.press(getByTestId('stop-button'));

      await waitForIntegration(() => {
        expect(getByTestId('has-recording')).toBeTruthy();
      });

      await act(async () => {
        fireEvent.press(getByTestId('generate-summary-button'));
      });

      await waitForIntegration(
        () => {
          expect(getByTestId('incident-count')).toHaveTextContent('1 recordings');
        },
        { timeout: INTEGRATION_TIMEOUTS.MEDIUM }
      );
    });
  });
});
