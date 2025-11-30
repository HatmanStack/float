import React from 'react';
import { Pressable } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { Colors } from '@/constants/Colors';
import useStyles from '@/constants/StylesConstants';
import { Audio } from 'expo-av';

/**
 * Props for RecordButton component
 */
interface RecordButtonProps {
  recording: Audio.Recording | null;
  handleStartRecording: () => void;
  handleStopRecording: () => void;
  errorText: boolean;
}

/**
 * Recording button component with start/stop functionality
 */
const RecordButton: React.FC<RecordButtonProps> = ({
  recording,
  handleStartRecording,
  handleStopRecording,
  errorText,
}: RecordButtonProps): React.ReactNode => {
  const styles = useStyles();

  return (
    <ThemedView style={{ flexDirection: 'column' }}>
      <Pressable
        onPress={() => (recording ? handleStopRecording() : handleStartRecording())}
        style={({ pressed }) => [
          {
            backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
          },
          styles.button,
        ]}
      >
        {({ pressed }) => (
          <ThemedText type="generate">
            {recording
              ? pressed
                ? 'STOP RECORDING'
                : 'Stop Recording'
              : pressed
                ? 'RECORDING!'
                : 'Record Audio'}
          </ThemedText>
        )}
      </Pressable>
      {errorText && <ThemedText type="details">Microphone is not available</ThemedText>}
      {recording && <ThemedText type="details">Recording...</ThemedText>}
    </ThemedView>
  );
};

export default RecordButton;
