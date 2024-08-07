import React from 'react';
import { Pressable, ActivityIndicator } from 'react-native';
import { StyleSheet } from 'react-native'; // Assuming these are custom components
import { ThemedText } from '@/components/ThemedText';

const MeditationControls = ({ isCalling, isPlaying, meditationURI, handlePlayMeditation, handleMeditationCall }) => (
  isCalling || isPlaying ? (
    <ActivityIndicator size="large" color="#B58392" />
  ) : (
    meditationURI ? (
      <Pressable onPress={handlePlayMeditation}
        style={({ pressed }) => [
          { backgroundColor: pressed ? "#958DA5" : "#9DA58D" },
          styles.button
        ]}>{({ pressed }) => (
        <ThemedText type="generate">{pressed ? "MEDITATE!" : "Play"}</ThemedText>
      )}
      </Pressable>
    ) : (
      <Pressable onPress={handleMeditationCall}
        style={({ pressed }) => [
          { backgroundColor: pressed ? "#958DA5" : "#9DA58D" },
          styles.button
        ]}>{({ pressed }) => (
        <ThemedText type="generate">{pressed ? "GENERATING!" : "Generate"}</ThemedText>
      )}
      </Pressable>
    )
  )
);

const styles = StyleSheet.create({
    button: {
      padding: 20,
      borderRadius: 20,
      width: 200,
      alignSelf: 'center'
    }
  });

export default MeditationControls;