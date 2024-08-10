import { Audio } from "expo-av";
import React, { useState } from "react";
import { Pressable, ActivityIndicator } from "react-native";
import { Colors } from "@/constants/Colors";
import useStyles from "@/constants/StylesConstants";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";

const MeditationControls = ({
  isCalling,
  meditationURI,
  handleMeditationCall
}) => {
  const [isPausing, setisPausing] = useState(false);
  const [sound, setSound] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const styles = useStyles();
  console.log("MeditationControls", isCalling, isPlaying, meditationURI);

  const handlePlayMeditation = async () => {
    try {
      let uri = meditationURI;
      if (uri.startsWith("blob:")) {
        const response = await fetch(uri);
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        uri = blobUrl;
      }

      if (sound) {
        if (isPausing) {
          await sound.pauseAsync();
          setisPausing(false);
          console.log("Paused the file:", uri);
        } else {
          await sound.playAsync();
          setisPausing(true);
          console.log("Resumed the file:", uri);
        }
      } else {
        const { sound: newSound } = await Audio.Sound.createAsync({ uri });
        setSound(newSound);
        newSound.setOnPlaybackStatusUpdate(async (status) => {
          if (status.didJustFinish) {
            console.log("Audio file finished playing");
            setIsPlaying(false);
            setSound(null);
          }
        });
        await newSound.playAsync();
        setIsPlaying(true);
        setisPausing(true);
        console.log("Playing the file:", uri);
      }
    } catch (error) {
      console.error("Error handling the audio file:", error);
    }
  };

  return isCalling ? (
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
        styles.button,
      ]}
    >
      {({ pressed }) => (
        <ThemedText type="generate">
          {isPausing ? (pressed ? "PAUSING": "Pause") : pressed ? "MEDITATE!" : "Play"}
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

export default MeditationControls