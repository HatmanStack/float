import Ionicons from '@expo/vector-icons/Ionicons';
import { StyleSheet, Pressable, ActivityIndicator } from 'react-native';
import React, { useState, useEffect } from 'react';
import { Collapsible } from '@/components/Collapsible';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { getMeditation } from '@/components/BackendMeditationCall'
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { useIncident } from '@/context/IncidentContext';


export default function TabTwoScreen() {
  const { incidentList, colorChangeSingleArray } = useIncident();
  const [renderKey, setRenderKey] = useState(0);
  const [selectedIndexes, setSelctedIndexes] = useState([]);
  const [meditationURI, setMeditationURI] = useState(null);
  const [isCalling, setIsCalling] = useState<null | 'calling'>(null);
  const [isPlaying, setIsPlaying] = useState<null | 'playing'>(null);
  
  useEffect(() => {
    if (renderKey < incidentList.length) {
    setRenderKey(prevKey => prevKey + 1);
    }
  }, [colorChangeSingleArray]);

  const handlePress = (index) => () => {
    setSelctedIndexes(prevIndexes => {
      if (prevIndexes.includes(index)) {
        return prevIndexes.filter(i => i !== index);
      }
      if (prevIndexes.length < 4){
        return [...prevIndexes, index];
      }
      return prevIndexes;
    }
  );
  }

  useEffect(() => {
    if(isCalling) {
      getMeditation(selectedIndexes).then((response) => {
        setMeditationURI(response);
      });
      setIsCalling(null);
    }
  }, [isCalling]);

  const handleMeditationCall = () => {
    console.log('called')
    if (selectedIndexes.length === 0) {
      return;
    }
    setIsCalling('calling');
  }

  useEffect(() => {
    if (isPlaying){
      playMeditation();
    }
  }
  , [isPlaying]);

  const handlePlayMeditation = () => {
    console.log('play');
    if (!meditationURI){
      return;
    }
    setIsPlaying('playing')
  }

const playMeditation = async () => {
  try {
    const { sound } = await Audio.Sound.createAsync({ uri: meditationURI });
    sound.setOnPlaybackStatusUpdate(async (status) => {
      if (status.didJustFinish) {
        console.log('Audio file finished playing');
        try {
          await FileSystem.deleteAsync(meditationURI);
          console.log('File deleted successfully');
        } catch (error) {
          console.error('Error deleting the file:', error);
        }
        setIsPlaying(null); 
        setMeditationURI(null);
      }
    });
    await sound.playAsync();
    console.log('Playing the file:', meditationURI);
  } catch (error) {
    console.error('Error handling the audio file:', error);
  }
};

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#D0D0D0', dark: '#353636' }}
      headerImage={<Ionicons size={310} name="list" style={styles.headerImage} />}>
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Discovery</ThemedText>
      </ThemedView>
      <Collapsible title="Guidance">
        <ThemedText type="body">Tap on the text to view the incident details</ThemedText>
        <ThemedText type="body">This selects the incident</ThemedText>
        <ThemedText type="body">You can select up to 3 incidents at a time</ThemedText>
        <ThemedText type="body">Tap on generate to create a personal meditation about the selected incidents</ThemedText>
        <ThemedText type="body">The color change of the incident represents how much time has past</ThemedText>
        <ThemedText type="body">The green incidents are ready to be dealt with</ThemedText>
      </Collapsible>
      
      {incidentList.map((incident, index) => {
        if (!incident) return null;
        const generatedText = incident.sentiment_label;
        const timestamp = new Date(incident.timestamp).toLocaleString();
        const displayText = selectedIndexes.includes(index) ? incident.user_summary : `${generatedText} - ${timestamp}`;

        return (
          <Pressable onPress={handlePress(index)} key={`${timestamp}-${renderKey}`} style={{ backgroundColor: colorChangeSingleArray[index] || '#FFFFFF', 
  padding: selectedIndexes.includes(index) ? 50 : 30 }}>
            <ThemedText  style={{ color: '#ffffff' }}>
            {displayText}
            </ThemedText>
            <Collapsible title="Details">
              <ThemedText type="body">{incident.intensity}</ThemedText>
              <ThemedText type="body">{incident.summary}</ThemedText>
            </Collapsible>
          </Pressable>
        );
      })}
      
      {isCalling || isPlaying ? (
      <ActivityIndicator size="large" color="#B58392"  />
        ) : (
          meditationURI ? (
            <Pressable onPress={handlePlayMeditation}
              style={({ pressed }) => [
                {backgroundColor: pressed ? "#958DA5" : "#9DA58D"},
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
        )}
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  headerImage: {
    color: '#808080',
    bottom: -90,
    left: -35,
    position: 'absolute',
  },
  titleContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  button: {
    padding: 20,
    borderRadius: 20,
    width: 200,
    alignSelf: 'center'
  }
});
