import React from "react";
import { Pressable } from "react-native";
import { ThemedText } from "@/frontend/components/ThemedText";
import { ThemedView } from "@/frontend/components/ThemedView";
import { Colors } from "@/frontend/constants/Colors";
import useStyles from "@/frontend/constants/StylesConstants";
import { Audio } from "expo-av";
interface RecordButtonProps {
  recording: Audio.Recording | null;
  handleStartRecording: () => void;
  handleStopRecording: () => void;
  errorText: boolean;
}
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
