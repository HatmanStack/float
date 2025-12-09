/**
 * MeditationLoading - Loading states component for streaming meditation
 * Provides contextual loading messages during meditation generation
 */

import React from 'react';
import { ActivityIndicator } from 'react-native';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';
import { Colors } from '@/constants/Colors';

export type LoadingState = 'starting' | 'preparing' | 'ready' | 'streaming';

export interface MeditationLoadingProps {
  state: LoadingState;
  segmentsCompleted?: number;
  segmentsTotal?: number | null;
}

/**
 * Get loading message for current state
 */
function getLoadingMessage(state: LoadingState): string {
  switch (state) {
    case 'starting':
      return 'Starting meditation...';
    case 'preparing':
      return 'Preparing audio...';
    case 'ready':
      return 'Ready to play';
    case 'streaming':
      return 'Streaming...';
    default:
      return 'Loading...';
  }
}

/**
 * MeditationLoading component for displaying streaming-aware loading states.
 * Shows contextual messages and optional progress.
 */
const MeditationLoading: React.FC<MeditationLoadingProps> = ({
  state,
  segmentsCompleted,
  segmentsTotal,
}) => {
  const message = getLoadingMessage(state);
  const showProgress = state === 'streaming' && segmentsCompleted !== undefined;
  const hasTotal = segmentsTotal !== undefined && segmentsTotal !== null && segmentsTotal > 0;

  return (
    <ThemedView
      style={{
        padding: 20,
        alignItems: 'center',
        justifyContent: 'center',
      }}
      testID="meditation-loading"
    >
      <ActivityIndicator
        size="large"
        color={Colors['activityIndicator']}
        testID="meditation-loading-indicator"
      />

      <ThemedText
        type="default"
        style={{ textAlign: 'center', marginTop: 15 }}
        testID="meditation-loading-message"
      >
        {message}
      </ThemedText>

      {showProgress && (
        <ThemedText
          type="default"
          style={{
            textAlign: 'center',
            marginTop: 8,
            opacity: 0.7,
            fontSize: 12,
          }}
          testID="meditation-loading-progress"
        >
          {hasTotal
            ? `${segmentsCompleted}/${segmentsTotal} segments`
            : `${segmentsCompleted} segments loaded`}
        </ThemedText>
      )}
    </ThemedView>
  );
};

export default MeditationLoading;
export { getLoadingMessage };
