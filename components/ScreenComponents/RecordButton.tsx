import React from "react";
import { Pressable, View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import { Colors } from "@/constants/Colors";
import useStyles from "@/constants/StylesConstants";

const RecordButton = ({
  recording,
  handleStartRecording,
  handleStopRecording,
  errorText,
}) => {
  const styles = useStyles(); // Call useStyles inside the component

  return (
    <ThemedView style={{ flexDirection: "column" }}>
      <Pressable
        onPress={recording ? handleStopRecording : handleStartRecording}
        style={({ pressed }) => [
          {
            backgroundColor: pressed
              ? Colors["buttonPressed"]
              : Colors["buttonUnpressed"],
          },
          styles.button,
        ]}
      >
        {({ pressed }) => (
          <ThemedText type="generate">
            {recording
              ? pressed
                ? "STOP RECORDING"
                : "Stop Recording"
              : pressed
              ? "RECORDING!"
              : "Record Audio"}
          </ThemedText>
        )}
      </Pressable>
      {errorText && (
        <ThemedText type="details">Microphone is not available</ThemedText>
      )}
      {recording && <ThemedText type="details">Recording...</ThemedText>}
    </ThemedView>
  );
};

export default RecordButton;
