import { Colors } from "@/constants/Colors";
import { useEffect } from "react";
import { useIncident } from "@/context/IncidentContext";

export function IncidentColoring() {
  const { incidentList, setColorChangeArrayOfArrays } = useIncident();

  const numberOfColorsToTransitionThrough = 3;

  const intensityMapping = {
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
  };
  const intensityTotalTimes = {
    1: [40, 600],
    2: [78, 1170],
    3: [116, 1740],
    4: [154, 2310],
    5: [192, 2880],
  };

  const getColorForIncident = (incident) => {
    const colorSet =
      Colors[incident.sentiment_label.toLowerCase()] || Colors.neutral;
    const colorSetKey = intensityMapping[incident.intensity] || "one";
    return colorSet[colorSetKey];
  };

  useEffect(() => {
    const processIncidents = async () => {
      setColorChangeArrayOfArrays([]);

      for (const [index, incident] of incidentList.entries()) {
        if (!incident) return null;
        try {
          const colorSets = getColorForIncident(incident);
          const incidentIntensityTimeCap =
            intensityTotalTimes[incident.intensity];
          const incidentTimestamp = new Date(incident.timestamp);
          const currentTime = new Date();
          const timeDifference = Math.abs(
            currentTime.getTime() - incidentTimestamp.getTime()
          );
          const timeDifferenceInMinutes = timeDifference / (1000 * 60);
          const colorKey =
            incidentIntensityTimeCap[0] -
            Math.round(
              (incidentIntensityTimeCap[1] - timeDifferenceInMinutes) / 15
            );
          if (colorKey !== incident.color_key) {
            incident.color_key = colorKey;
          }
          const intensity =
            incident.intensity === "1" ? "2" : incident.intensity;
          const endIndex = Math.min(
            colorKey + parseInt(intensity) * numberOfColorsToTransitionThrough,
            colorSets.length
          );
          const incidentBackgroundColorArray = colorSets.slice(
            colorKey,
            endIndex
          );
          setColorChangeArrayOfArrays((prevColors) => {
            return [...prevColors, incidentBackgroundColorArray];
          });
        } catch (error) {
          console.error("Invalid JSON:", error);
          return null;
        }
      }
    };

    processIncidents();
  }, [incidentList]);

  return null;
}
