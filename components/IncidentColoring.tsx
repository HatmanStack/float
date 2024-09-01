import { Colors } from "@/constants/Colors";
import { useEffect } from "react";
import { useIncident } from "@/context/IncidentContext";
import { getCurrentTime } from '@/constants/util';

export function IncidentColoring() {
  const { incidentList, setColorChangeArrayOfArrays } = useIncident();

  const numberOfColorsToTransitionThrough = 10;

  const intensityMapping = {
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
  };
  const intensityTotalTimes = {
    1: [40,600],
    2: [70,1050],
    3: [110,1650],
    4: [150,2250],
    5: [190,2850]
  }

  const getColorForIncident = (incident) => {
    const colorSet =
      Colors[incident.sentiment_label.toLowerCase()] || Colors.neutral;
    const colorSetKey = intensityMapping[incident.intensity] || "one";
    return colorSet[colorSetKey];
  };

  useEffect(() => {
    const processIncidents = async () => {
      let arrayHolder = [];
      for (const [index, incident] of incidentList.entries()) {
        if (!incident) return null;
        try {
          const colorSets = getColorForIncident(incident);
          const incidentTimestamp = new Date(incident.timestamp);
          const currentTime = getCurrentTime();
          if(!currentTime) return null;

          const timeDifference = currentTime.getTime() - incidentTimestamp.getTime();
          const timeDifferenceInMinutes = timeDifference / (1000 * 60);          
          const colorKey = timeDifferenceInMinutes > intensityTotalTimes[incident.intensity][1] ? 
          intensityTotalTimes[incident.intensity][0] :  timeDifferenceInMinutes / 15;

          if (colorKey !== incident.color_key) {
            incident.color_key = colorKey;
          }
          
          const endIndex = Math.min(
            colorKey + numberOfColorsToTransitionThrough,
            colorSets.length
          );
          const incidentBackgroundColorArray = colorSets.slice(
            colorKey,
            endIndex
          );
          
          arrayHolder = [...arrayHolder, incidentBackgroundColorArray]; 
        } catch (error) {
          console.error("Invalid JSON:", error);
          return null;
        }
      }
      setColorChangeArrayOfArrays(arrayHolder);
    };

    processIncidents();
  }, [incidentList]);

  return null;
}
