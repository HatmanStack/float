import { Audio } from 'expo-av';
import React, { useState, useCallback } from 'react';
import { Pressable, ActivityIndicator } from 'react-native';
import { Colors } from "@/frontend/constants/Colors';
import useStyles from "@/frontend/constants/StylesConstants';
import { ThemedText } from "@/frontend/components/ThemedText';
import { ThemedView } from "@/frontend/components/ThemedView';
interface MeditationControlsProps {
  isCalling: boolean;
  meditationURI: string;
  setMeditationURI: (uri: string) => void;
  handleMeditationCall: () => void;
}
function useAudioPlayback(meditationURI: string, setMeditationURI: (uri: string) => void) {
  const [isPausing, setisPausing] = useState(false);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const handlePlayMeditation = useCallback(async () => {
    try {
      let uri = meditationURI;
      if (uri.startsWith('blob:')) {
        const response = await fetch(uri);
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        uri = blobUrl;
      }
      if (sound) {
        if (isPausing) {
          await sound.pauseAsync();
          setisPausing(false);
          console.log('Paused the file:', uri);
        } else {
          await sound.playAsync();
          setisPausing(true);
          console.log('Resumed the file:', uri);
        }
      } else {
        const { sound: newSound } = await Audio.Sound.createAsync({ uri });
        setSound(newSound);
        newSound.setOnPlaybackStatusUpdate(async (status) => {
          if ('didJustFinish' in status && status.didJustFinish) {
            console.log('Audio file finished playing');
            try {
              await newSound.unloadAsync();
            } catch (error) {
              console.error('Error unloading audio:', error);
            }
            setisPausing(false);
            setSound(null);
            setMeditationURI('');
          }
        });
        await newSound.playAsync();
        setisPausing(true);
        console.log('Playing the file:', uri);
      }
    } catch (error) {
      console.error('Error handling the audio file:', error);
    }
  }, [meditationURI, sound, isPausing, setMeditationURI]);
  return {
    isPausing,
    handlePlayMeditation,
  };
}
const MeditationControls: React.FC<MeditationControlsProps> = ({
  isCalling,
  meditationURI,
  setMeditationURI,
  handleMeditationCall,
}: MeditationControlsProps): React.JSX.Element => {
  const styles = useStyles();
  const { isPausing, handlePlayMeditation } = useAudioPlayback(meditationURI, setMeditationURI);
  return isCalling ? (
    <ThemedView style={{ padding: 50 }}>
      <ActivityIndicator
        size="large"
        color={Colors['activityIndicator']}
        testID="activity-indicator"
      />
    </ThemedView>
  ) : meditationURI ? (
    <Pressable
      onPress={handlePlayMeditation}
      style={({ pressed }) => [
        {
          backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
        },
        styles.button,
      ]}
    >
      {({ pressed }) => (
        <ThemedText type="generate">
          {isPausing ? (pressed ? 'PAUSING' : 'Pause') : pressed ? 'MEDITATE!' : 'Play'}
        </ThemedText>
      )}
    </Pressable>
  ) : (
    <Pressable
      onPress={handleMeditationCall}
      style={({ pressed }) => [
        {
          backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
        },
        styles.button,
      ]}
    >
      {({ pressed }) => (
        <ThemedText type="generate">{pressed ? 'GENERATING!' : 'Generate Meditation'}</ThemedText>
      )}
    </Pressable>
  );
};
export default MeditationControls;
