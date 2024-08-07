import { Colors } from '@/constants/Colors';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useState, useEffect } from 'react';
import { useIncident } from '@/context/IncidentContext';

export function IncidentColoring() {
    const [colorChangeArrayOfArrays, setcolorChangeArrayOfArrays] = useState([]);
    const { incidentList, setColorChangeSingleArray } = useIncident();

  const intensityMapping = {
    '1': 'one',
    '2': 'two',
    '3': 'three',
    '4': 'four',
    '5': 'five'
  };
  const intensityTotalTimes = {
    1: [40,600], 
    2: [78,1170], 
    3: [116,1740], 
    4: [154,2310], 
    5: [192,2880], 
  };

  const getColorForIncident = (incident) => {
    const colorSet = Colors[incident.sentiment_label.toLowerCase()] || Colors.neutral;
    const colorSetKey = intensityMapping[incident.intensity] || 'one'; 
    return colorSet[colorSetKey]; 
};

  useEffect(() => {
    const processIncidents = async () => {
      
      for (const [index, incidentPromise] of incidentList.entries()) {
        
        const holderIncident = await Promise.resolve(incidentPromise);
      if (!holderIncident) return null;
      console.log('ProcessIncidents', holderIncident);
      const incident = JSON.parse(holderIncident);
      const colorSets = getColorForIncident(incident);
      const incidentIntensityTimeCap = intensityTotalTimes[incident.intensity];
      const incidentTimestamp = new Date(incident.timestamp);
      const currentTime = new Date();
      const timeDifference = Math.abs(currentTime.getTime() - incidentTimestamp.getTime());
      const timeDifferenceInMinutes = timeDifference / (1000 * 60);
  
      const colorKey = (incidentIntensityTimeCap[0] - Math.round((incidentIntensityTimeCap[1] - timeDifferenceInMinutes) / 15));
      if (colorKey !== incident.color_key) {
        incident.color_key = colorKey;
      }
      const endIndex = Math.min(colorKey + parseInt(incident.intensity) * 12, colorSets.length);
      const incidentBackgroundColorArray = colorSets.slice(colorKey, endIndex);
      
      setcolorChangeArrayOfArrays(prevColors => {
        return [...prevColors, incidentBackgroundColorArray];
      });
      }
    };
    
    processIncidents()
  }, [incidentList]);


  useEffect(() => {
    if (!colorChangeArrayOfArrays || colorChangeArrayOfArrays.length === 0) return;
  
    let currentIndexes = new Array(colorChangeArrayOfArrays.length).fill(0);
    let directions = new Array(colorChangeArrayOfArrays.length).fill(1);
  
    const interval = setInterval(() => {
      setColorChangeSingleArray(prevColors => {
        const newColors = [...prevColors];
  
        colorChangeArrayOfArrays.forEach((colorArray, index) => {
          if (!colorArray || colorArray.length === 0) return;
  
          if (currentIndexes[index] >= colorArray.length - 3) {
            directions[index] = -1;
          } else if (currentIndexes[index] <= 0) {
            directions[index] = 1;
          }
          currentIndexes[index] += directions[index];
  
          newColors[index] = colorArray[currentIndexes[index]];
        });
  
        return newColors;
      });
    }, 500);
  
    return () => clearInterval(interval);
  }, [colorChangeArrayOfArrays]);

  return null;
}
