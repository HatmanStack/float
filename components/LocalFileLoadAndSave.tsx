import AsyncStorage from '@react-native-async-storage/async-storage';
import { useIncident } from '@/context/IncidentContext';
import { useEffect } from 'react';

export function IncidentSave() {
  const { incidentList, setIncidentList, musicList, setMusicList } = useIncident();

  useEffect(() => {
    const loadIncidentList = async () => {
      try {
        const storedIncidentList = await AsyncStorage.getItem('incidentList');
        const storedMusicList = await AsyncStorage.getItem('musicList');
        if (storedIncidentList) {
          const parsedIncidentList = JSON.parse(storedIncidentList);
          const reversedIncidentList = parsedIncidentList.reverse();
          console.log('Loaded and reversed incident list:', reversedIncidentList);
          setIncidentList(reversedIncidentList);
        }
        if (storedMusicList) {
          const parsedMusicList = storedMusicList;
          console.log('Loaded music list:', parsedMusicList);
          setMusicList(parsedMusicList);
        }
      } catch (error) {
        console.error('Failed to load incident list:', error);
      }
    };

    loadIncidentList();
  }, []);

  useEffect(() => {
    const saveIncidentList = async () => {
      try {
        await AsyncStorage.setItem('incidentList', JSON.stringify(incidentList));
        console.log('Saved incident list');
      } catch (error) {
        console.error('Failed to save incident list:', error);
      }
    };

    saveIncidentList();
  }, [incidentList]);

  useEffect(() => {
    const saveMusicList = async () => {
      try {
        await AsyncStorage.setItem('musicList', JSON.stringify(musicList));
        console.log('Saved music list');
      } catch (error) {
        console.error('Failed to save music list:', error);
      }
    };

    saveMusicList();
  }, [musicList]);
  return null;
}
