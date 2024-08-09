import Ionicons from '@expo/vector-icons/Ionicons';
import { StyleSheet, useWindowDimensions } from 'react-native';
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
import { GestureHandlerRootView, Swipeable } from 'react-native-gesture-handler';


export default function TabTwoScreen() {
  const { incidentList, setIncidentList, colorChangeSingleArray, musicList, setMusicList } = useIncident();
  const [renderKey, setRenderKey] = useState(0);
  const [selectedIndexes, setSelctedIndexes] = useState([]);
  const [asyncDeleteIncident, setAsyncDeleteIncident] = useState(null);
  const [meditationURI, setMeditationURI] = useState('');
  const [isCalling, setIsCalling] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [openIndexes, setOpenIndexes] = useState({});
  const { width, height } = useWindowDimensions();

  useEffect(() => {
  }, [width, height]);

  const toggleCollapsible = (index) => {
    setOpenIndexes((prev) => ({ ...prev, [index]: !prev[index] }));
  };
  
  useEffect(() => {
    setRenderKey(prevKey => prevKey + 1);
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
    const fetchData = async () => {
      if (isCalling) {
        try {
          const response = await BackendMeditationCall(selectedIndexes, incidentList, musicList);
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

  useEffect(() => {
    if(asyncDeleteIncident !== null){
      setIncidentList(prevIncidents => prevIncidents.filter((_, i) => i !== asyncDeleteIncident));
      setAsyncDeleteIncident(null);
    }
  }, [asyncDeleteIncident]);
 

  const renderRightActions = (index) => {
    return (
      <ThemedView style={{ justifyContent: 'center' }}>
        <ThemedText type="subtitle" onPress={() => setAsyncDeleteIncident(index)}>Delete</ThemedText>
      </ThemedView>
    );
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#bfaeba', dark: '#60465a' }}
      headerImage={<Ionicons size={310} name="list" style={styles.headerImage}/>}
      headerText={<ThemedText type="header">FLOAT</ThemedText>}
      >
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Discovery</ThemedText>
      </ThemedView>
      <Guidance />
    {incidentList.map((incident, index) => {
      if (!incident){
        handleDeleteIncident(index);
        return null;
      } 
      const timestamp = new Date(incident.timestamp).toLocaleString();
      const uniqueKey = timestamp + renderKey;
      return (
        
        <Swipeable
              key={uniqueKey + 'swipeable'}
              renderRightActions={() => renderRightActions(index)}
            >
        <IncidentItem
          key={uniqueKey}
          renderKey={uniqueKey}
          incident={incident}
          index={index}
          selectedIndexes={selectedIndexes}
          handlePress={handlePress}
          isOpen={!!openIndexes[index]}
          toggleCollapsible={() => toggleCollapsible(index)}
        />
        </Swipeable>
        
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
    </GestureHandlerRootView>
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
