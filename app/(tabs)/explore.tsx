import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { useWindowDimensions, Platform } from "react-native";
import * as React from "react";
import { useState, useEffect } from "react";
import * as Notifications from 'expo-notifications';
import ParallaxScrollView from "@/components/ParallaxScrollView";
import { BackendMeditationCall } from "@/components/BackendMeditationCall";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import { useIncident } from "@/context/IncidentContext";
import { useAuth } from '@/context/AuthContext';
import Guidance from "@/components/ScreenComponents/Guidance";
import IncidentItem from "@/components/ScreenComponents/IncidentItem";
import MeditationControls from "@/components/ScreenComponents/MeditationControls";
import useStyles from "@/constants/StylesConstants";

import {
  GestureHandlerRootView,
  Swipeable,
} from "react-native-gesture-handler";

export default function TabTwoScreen() {
  const {
    incidentList,
    setIncidentList,
    colorChangeArrayOfArrays,
    musicList,
    setMusicList,
  } = useIncident();
  const [renderKey, setRenderKey] = useState(0);
  const [selectedIndexes, setSelctedIndexes] = useState([]);
  const [asyncDeleteIncident, setAsyncDeleteIncident] = useState(null);
  const [meditationURI, setMeditationURI] = useState("");
  const [isCalling, setIsCalling] = useState(false);
  const [openIndexes, setOpenIndexes] = useState({});
  const { width, height } = useWindowDimensions();
  const { user } = useAuth();
  const styles = useStyles();
  useEffect(() => {}, [width, height]);

  const toggleCollapsible = (index) => {
    setOpenIndexes((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  useEffect(() => {
    setRenderKey((prevKey) => prevKey + 1);
  }, [colorChangeArrayOfArrays]);

  const handlePress = (index) => () => {
    console.log("handlePress", index);
    setSelctedIndexes((prevIndexes) => {
      if (prevIndexes.includes(index)) {
        return prevIndexes.filter((i) => i !== index);
      }
      if (prevIndexes.length < 4) {
        return [...prevIndexes, index];
      }
      return prevIndexes;
    });
  };

  useEffect(() => {
    const fetchData = async () => {
      if (isCalling) {
        try {
          const response = await BackendMeditationCall(
            selectedIndexes,
            incidentList,
            musicList,
            user
          );
          setMeditationURI(response.responseMeditationURI);
          setMusicList(response.responseMusicList);
        } catch (error) {
          console.error("Error fetching data:", error);
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
  };

  useEffect(() => {
    if (asyncDeleteIncident !== null) {
      setIncidentList((prevIncidents) =>
        prevIncidents.filter((_, i) => i !== asyncDeleteIncident)
      );
      setAsyncDeleteIncident(null);
  
      async function cancelScheduledNotification(notificationId) {
        await Notifications.cancelScheduledNotificationAsync(notificationId);
        console.log('Notification canceled with ID:', notificationId);
      }
      if (Platform.OS !== 'web') {
      cancelScheduledNotification(incidentList[asyncDeleteIncident].notificationId);
      }
    }
  }, [asyncDeleteIncident]);;

  const handleDeleteIncident = (index) => {
    setAsyncDeleteIncident(index);
  };

  const renderRightActions = (index) => {
    return (
      <ThemedView style={{ justifyContent: "center" }}>
        <ThemedText
          type="subtitle"
          onPress={() => setAsyncDeleteIncident(index)}
        >
          Delete
        </ThemedText>
      </ThemedView>
    );
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ParallaxScrollView
        headerBackgroundColor={{ light: "#bfaeba", dark: "#60465a" }}
        headerImage={
          <MaterialIcons size={310} name="self-improvement" style={styles.headerImage} />
        }
        headerText={<ThemedText type="header">fLoAt</ThemedText>}
      >
        <ThemedView style={styles.titleContainer}>
          <ThemedText type="title">Discovery</ThemedText>
        </ThemedView>
        <Guidance />
        {incidentList.map((incident, index) => {
          if (!incident) {
            handleDeleteIncident(index);
            return null;
          }
          
          const timestamp = new Date(incident.timestamp).toLocaleString();
          const uniqueKey = timestamp + renderKey;
          return (
            <Swipeable
              key={uniqueKey + "swipeable"}
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
                colorChangeArrayOfArrays={colorChangeArrayOfArrays}
              />
            </Swipeable>
          );
        })}
        <MeditationControls
          isCalling={isCalling}
          meditationURI={meditationURI}
          setMeditationURI={setMeditationURI}
          handleMeditationCall={handleMeditationCall}
        />
      </ParallaxScrollView>
    </GestureHandlerRootView>
  );
}
