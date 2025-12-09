/**
 * StreamingError - Error display component for HLS streaming errors
 * Provides user-friendly error messages and retry functionality
 */

import React from 'react';
import { Pressable } from 'react-native';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';
import { Colors } from '@/constants/Colors';

export interface StreamingErrorProps {
  error: Error;
  onRetry: () => void;
  canRetry?: boolean;
}

/**
 * Map error types to user-friendly messages
 */
function getErrorMessage(error: Error): string {
  const message = error.message.toLowerCase();

  // Network errors
  if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
    return 'Connection lost. Check your internet and try again.';
  }

  // HLS specific errors
  if (message.includes('hls') || message.includes('manifest') || message.includes('playlist')) {
    return 'Playback failed. Tap retry to start over.';
  }

  // Download errors (check before generation to avoid 'failed' matching 'Download failed')
  if (message.includes('download')) {
    return 'Download failed. Tap to retry.';
  }

  // Generation errors
  if (message.includes('generation') || message.includes('timeout')) {
    return 'Could not generate meditation. Please try again.';
  }

  // Default message
  return 'Something went wrong. Please try again.';
}

/**
 * StreamingError component for displaying streaming/playback errors
 * with user-friendly messages and retry support.
 */
const StreamingError: React.FC<StreamingErrorProps> = ({
  error,
  onRetry,
  canRetry = true,
}) => {
  const userMessage = getErrorMessage(error);

  return (
    <ThemedView style={{ padding: 20, alignItems: 'center' }} testID="streaming-error">
      <ThemedText
        type="default"
        style={{ textAlign: 'center', marginBottom: 10 }}
        testID="streaming-error-message"
      >
        {userMessage}
      </ThemedText>

      {canRetry && (
        <Pressable
          onPress={onRetry}
          style={({ pressed }) => ({
            backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
            paddingHorizontal: 20,
            paddingVertical: 10,
            borderRadius: 8,
            marginTop: 10,
          })}
          testID="streaming-error-retry-button"
        >
          <ThemedText type="generate">Retry</ThemedText>
        </Pressable>
      )}

      {/* Debug info in development */}
      {__DEV__ && (
        <ThemedText
          type="default"
          style={{ textAlign: 'center', marginTop: 20, opacity: 0.5, fontSize: 10 }}
        >
          Debug: {error.message}
        </ThemedText>
      )}
    </ThemedView>
  );
};

export default StreamingError;
export { getErrorMessage };
