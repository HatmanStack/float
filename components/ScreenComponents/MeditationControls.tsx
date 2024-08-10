import React from "react";
import { Pressable, ActivityIndicator } from "react-native";
import { Colors } from "@/constants/Colors";
import useStyles from "@/constants/StylesConstants"; // Ensure this is correct
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";

const MeditationControls = ({
  isCalling,
  isPlaying,
  meditationURI,
  handlePlayMeditation,
  handleMeditationCall,
}) => {
  const styles = useStyles(); 

  return isCalling || isPlaying ? (
    <ThemedView style={{ padding: 50 }}>
      <ActivityIndicator size="large" color={Colors["activityIndicator"]} />
    </ThemedView>
  ) : meditationURI ? (
    <Pressable
      onPress={handlePlayMeditation}
      style={({ pressed }) => [
        {
          backgroundColor: pressed
            ? Colors["buttonPressed"]
            : Colors["buttonUnpressed"],
        },
        styles.button, // Apply styles.button here
      ]}
    >
      {({ pressed }) => (
        <ThemedText type="generate">
          {pressed ? "MEDITATE!" : "Play"}
        </ThemedText>
      )}
    </Pressable>
  ) : (
    <Pressable
      onPress={handleMeditationCall}
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
          {pressed ? "GENERATING!" : "Generate Meditation"}
        </ThemedText>
      )}
    </Pressable>
  );
};

export default MeditationControls;
