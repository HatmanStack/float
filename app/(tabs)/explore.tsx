import Ionicons from '@expo/vector-icons/Ionicons';
import { StyleSheet } from 'react-native';
import React, { useState, useEffect } from 'react';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { BackendMeditationCall } from '@/components/BackendMeditationCall'
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { useIncident } from '@/context/IncidentContext';
import Guidance from '@/components/ScreenComponents/Guidance';
import IncidentItem from '@/components/ScreenComponents/IncidentItem';
import MeditationControls from '@/components/ScreenComponents/MeditationControls';
import playMeditation from '@/components/PlayMeditation';

export default function TabTwoScreen() {
  const { incidentList, colorChangeSingleArray, musicList, setMusicList } = useIncident();
  const [renderKey, setRenderKey] = useState(0);
  const [selectedIndexes, setSelctedIndexes] = useState([]);
  const [resolvedIncidents, setResolvedIncidents] = useState([]);
  const [meditationURI, setMeditationURI] = useState('');
  const [isCalling, setIsCalling] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  
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
    const resolveIncidents = async () => {
      const resolved = await Promise.all(incidentList);
      console.log('Resolved incidents:', resolved);
      setResolvedIncidents(resolved);
    };

    resolveIncidents();
  }, [incidentList]);

  useEffect(() => {
    const fetchData = async () => {
      if (isCalling) {
        try {
          const response = await BackendMeditationCall(selectedIndexes, resolvedIncidents, musicList);
          console.log('Response:', response);
          setMeditationURI(response.responseMeditationURI);
          setMusicList(response.responseMusicList);
        } catch (error) {
          console.error('Error fetching data:', error);
        } finally {
          setIsCalling(false);
        }
      }
    };

    fetchData();
  }, [isCalling]);

  const handleMeditationCall = () => {
    if (selectedIndexes.length === 0) {
      return;
    }
    setIsCalling(true);
  }

  useEffect(() => {
    if (isPlaying){
      playMeditation();
    }
  }
  , [isPlaying]);

  const handlePlayMeditation = () => {
    console.log('play');
    if (!meditationURI) {
      return;
    }
    setIsPlaying(true);
    playMeditation(meditationURI, setIsPlaying, setMeditationURI); // Call the playMeditation function
  };

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#D0D0D0', dark: '#353636' }}
      headerImage={<Ionicons size={310} name="list" style={styles.headerImage} />}>
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Discovery</ThemedText>
      </ThemedView>
      <Guidance />
    {resolvedIncidents.map((stringIncident, index) => {
      if (!stringIncident || stringIncident.length === undefined) return null;
      const incident = JSON.parse(stringIncident);
      return (
        <IncidentItem
          key={index}
          incident={incident}
          index={index}
          selectedIndexes={selectedIndexes}
          handlePress={handlePress}
          colorChangeSingleArray={colorChangeSingleArray}
        />
      );
    })}
    <MeditationControls
      isCalling={isCalling}
      isPlaying={isPlaying}
      meditationURI={meditationURI}
      handlePlayMeditation={handlePlayMeditation}
      handleMeditationCall={handleMeditationCall}
    />
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
  }
});
