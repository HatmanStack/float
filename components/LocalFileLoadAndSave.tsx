import AsyncStorage from '@react-native-async-storage/async-storage';
import { useIncident} from '@/context/IncidentContext';
import { useEffect } from 'react';

export default function IncidentSave() {
    const { incidentList, setIncidentList } = useIncident();

useEffect(() => {
    const loadIncidentList = async () => {
      try {
        const storedIncidentList = await AsyncStorage.getItem('incidentList');
        if (storedIncidentList) {
          const parsedIncidentList = JSON.parse(storedIncidentList);
          const reversedIncidentList = parsedIncidentList.reverse();
          console.log('Loaded and reversed incident list:', reversedIncidentList);
          setIncidentList(reversedIncidentList);
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
      } catch (error) {
        console.error('Failed to save emotion list:', error);
      }
    };

    saveIncidentList();
  }, [incidentList]);
  return null;
}