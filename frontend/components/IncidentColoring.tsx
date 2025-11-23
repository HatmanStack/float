import { Colors } from "@/frontend/constants/Colors";
import { useEffect } from "react";
import { useIncident, Incident } from "@/frontend/context/IncidentContext";
import { getCurrentTime } from "@/frontend/constants/StylesConstants";
export function IncidentColoring() {
  const { incidentList, setColorChangeArrayOfArrays } = useIncident();
  const numberOfColorsToTransitionThrough = 10;
  const intensityMapping: Record<number | string, string> = {
    1: 'one',
    2: 'two',
    3: 'three',
    4: 'four',
    5: 'five',
  };
  const intensityTotalTimes: Record<number, [number, number]> = {
    1: [40, 600],
    2: [70, 1050],
    3: [110, 1650],
    4: [150, 2250],
    5: [190, 2850],
  };
  const getColorForIncident = (incident: Incident): string[] => {
    const colorSet =
      Colors[incident.sentiment_label.toLowerCase() as keyof typeof Colors] || Colors.neutral;
    const intensityNum =
      typeof incident.intensity === 'string'
        ? parseInt(incident.intensity, 10)
        : incident.intensity;
    const colorSetKey = intensityMapping[intensityNum] || 'one';
    const result = colorSet[colorSetKey as keyof typeof colorSet];
    return Array.isArray(result) ? result : [];
  };
  useEffect(() => {
    const processIncidents = async () => {
      const arrayHolder: string[][] = [];
      for (const incident of incidentList) {
        if (!incident) continue;
        try {
          const colorSets = getColorForIncident(incident);
          const incidentTimestamp = new Date(incident.timestamp);
          const currentTime = getCurrentTime();
          if (!currentTime) continue;
          const timeDifference = currentTime.getTime() - incidentTimestamp.getTime();
          const timeDifferenceInMinutes = timeDifference / (1000 * 60);
          const intensityNum =
            typeof incident.intensity === 'string'
              ? parseInt(incident.intensity, 10)
              : incident.intensity;
          const intensityKey = Math.min(Math.max(intensityNum as number, 1), 5) as
            | 1
            | 2
            | 3
            | 4
            | 5;
          const colorKey =
            timeDifferenceInMinutes > intensityTotalTimes[intensityKey][1]
              ? intensityTotalTimes[intensityKey][0]
              : timeDifferenceInMinutes / 15;
          const endIndex = Math.min(colorKey + numberOfColorsToTransitionThrough, colorSets.length);
          const incidentBackgroundColorArray = colorSets.slice(colorKey, endIndex);
          arrayHolder.push(incidentBackgroundColorArray);
        } catch (error) {
          console.error('Invalid JSON:', error);
        }
      }
      setColorChangeArrayOfArrays(arrayHolder);
    };
    processIncidents();
  }, [incidentList, setColorChangeArrayOfArrays]);
  return null;
}
