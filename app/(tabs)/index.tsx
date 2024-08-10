import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { TextInput } from "react-native";
import React, { useState, useEffect } from "react";
import ParallaxScrollView from "@/components/ParallaxScrollView";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import RecordButton from "@/components/ScreenComponents/RecordButton";
import SubmitButton from "@/components/ScreenComponents/SubmitButton";
import { StartRecording, StopRecording } from "@/components/AudioRecording";
import { BackendSummaryCall } from "@/components/BackendSummaryCall";
import { useIncident } from "@/context/IncidentContext";
import { Audio } from "expo-av";
import useStyles from "@/constants/StylesConstants";

  
import { Platform, useWindowDimensions } from "react-native";

export default function HomeScreen() {
  const [separateTextPrompt, setSeparateTextPrompt] = useState("");
  const [recording, setRecording] = useState(null);
  const [URI, setURI] = useState("");
  const [errorText, setErrorText] = useState(false);
  const [summaryCall, setSummaryCall] = useState(false);
  const { setIncidentList } = useIncident();
  const { width, height } = useWindowDimensions();
  const styles = useStyles();

  useEffect(() => {}, [width, height]);

  const handleStartRecording = async () => {
    try {
      if (Platform.OS === "web") {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      } else {
        const { granted } = await Audio.requestPermissionsAsync();
        if (!granted) {
          throw new Error("Microphone permission not granted");
        }
      }
      const recording = await StartRecording();
      setRecording(recording);
      setErrorText(false);
    } catch (error) {
      console.error("Microphone is not available:", error);
      setErrorText(true);
    }
  };

  const handleStopRecording = async () => {
    const uri = await StopRecording(recording);
    setURI(uri);
    setRecording(null);
    console.log("Recording stopped and stored at:", uri);
  };

  const handleSummaryCall = async () => {
    setSummaryCall(true);
  };

  useEffect(() => {
    if (summaryCall) {
      const fetchData = async () => {
        if (!URI && !separateTextPrompt) {
          console.log(
            "Returning early due to null recording and empty separateTextPrompt"
          );
          setSummaryCall(false);
          return;
        }
        try {
          let response;
          if (recording) {
            const base64_file = await StopRecording(recording);
            response = await BackendSummaryCall(
              base64_file,
              separateTextPrompt
            );
          } else {
            response = await BackendSummaryCall(URI, separateTextPrompt);
          }
          setIncidentList((prevList) => [response, ...prevList]);
          setRecording(null);
          setURI("");
          setErrorText(false);
        } catch (error) {
          console.error("Failed to call summary lambda:", error);
        } finally {
          setSummaryCall(false);
        }
      };

      fetchData();
    }
  }, [summaryCall, URI, separateTextPrompt, recording, setIncidentList]);

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: "#bfaeba", dark: "#60465a" }}
      headerImage={
        <MaterialIcons
          size={310}
          name="self-improvement"
          style={styles.headerImage}
        />
      }
      headerText={<ThemedText type="header">FLOAT</ThemedText>}
    >
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Hey! How are you?</ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">
          Something Wrong? Tell me about it.
        </ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <TextInput
          style={styles.input}
          placeholder="Type or Chat"
          value={separateTextPrompt}
          multiline={true}
          textAlignVertical="top"
          onChangeText={setSeparateTextPrompt}
        />
        <ThemedView style={styles.homeButtonContainer}>
          <RecordButton
            recording={recording}
            handleStartRecording={handleStartRecording}
            handleStopRecording={handleStopRecording}
            errorText={errorText}
          />
          <SubmitButton
            summaryCall={summaryCall}
            handleSummaryCall={handleSummaryCall}
          />
        </ThemedView>
      </ThemedView>
    </ParallaxScrollView>
  );
}
