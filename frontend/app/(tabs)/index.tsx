import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { TextInput } from "react-native";
import React, { useState, useEffect, useCallback } from "react";
import ParallaxScrollView from "@/frontend/components/ParallaxScrollView";
import { ThemedText } from "@/frontend/components/ThemedText";
import { ThemedView } from "@/frontend/components/ThemedView";
import RecordButton from "@/frontend/components/ScreenComponents/RecordButton";
import SubmitButton from "@/frontend/components/ScreenComponents/SubmitButton";
import { StartRecording, StopRecording } from "@/frontend/components/AudioRecording";
import FloatNotifications from "@/frontend/components/Notifications";
import { BackendSummaryCall } from "@/frontend/components/BackendSummaryCall";
import { useIncident } from "@/frontend/context/IncidentContext";
import { Audio } from "expo-av";
import useStyles from "@/frontend/constants/StylesConstants";
import { Platform, useWindowDimensions } from "react-native";
import { useAuth } from "@/frontend/context/AuthContext";
import { useRouter } from "expo-router";
function useAudioRecording() {
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [URI, setURI] = useState('');
  const [errorText, setErrorText] = useState(false);
  const handleStartRecording = useCallback(async () => {
    try {
      if (Platform.OS === 'web') {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      } else {
        const { granted } = await Audio.requestPermissionsAsync();
        if (!granted) {
          throw new Error('Microphone permission not granted');
        }
      }
      const recording = await StartRecording();
      setRecording(recording ?? null);
      setErrorText(false);
    } catch (error) {
      console.error('Microphone is not available:', error);
      setErrorText(true);
    }
  }, []);
  const handleStopRecording = useCallback(async () => {
    if (recording) {
      const uri = await StopRecording(recording);
      setURI(typeof uri === 'string' ? uri : '');
      setRecording(null);
    }
  }, [recording]);
  const resetRecording = useCallback(() => {
    setRecording(null);
    setURI('');
    setErrorText(false);
  }, []);
  return {
    recording,
    URI,
    errorText,
    handleStartRecording,
    handleStopRecording,
    resetRecording,
  };
}
function useSummarySubmission(
  recording: Audio.Recording | null,
  URI: string,
  separateTextPrompt: string,
  onSubmitSuccess: () => void
) {
  const [summaryCall, setSummaryCall] = useState(false);
  const [submitActivity, setSubmitActivity] = useState(false);
  const { setIncidentList } = useIncident();
  const { user } = useAuth();
  const router = useRouter();
  const handleSummaryCall = useCallback(async () => {
    setSummaryCall(true);
    setSubmitActivity(true);
  }, []);
  useEffect(() => {
    if (summaryCall) {
      setSummaryCall(false);
      const fetchData = async () => {
        if (!URI && !separateTextPrompt) {
          console.log('Returning early due to null recording and empty separateTextPrompt');
          setSubmitActivity(false);
          return;
        }
        try {
          let response: any;
          if (recording) {
            const base64_file = await StopRecording(recording);
            response = await BackendSummaryCall(
              base64_file ?? '',
              separateTextPrompt,
              user?.id ?? ''
            );
          } else {
            response = await BackendSummaryCall(URI, separateTextPrompt, user?.id ?? '');
          }
          console.log('Response from summary lambda:', response);
          setIncidentList((prevList) => [response, ...prevList]);
          onSubmitSuccess();
        } catch (error) {
          console.error('Failed to call summary lambda:', error);
        } finally {
          setSubmitActivity(false);
          router.push('/explore');
        }
      };
      fetchData();
    }
  }, [
    summaryCall,
    URI,
    separateTextPrompt,
    recording,
    setIncidentList,
    user?.id,
    router,
    onSubmitSuccess,
  ]);
  return {
    submitActivity,
    handleSummaryCall,
  };
}
export default function HomeScreen(): React.ReactNode {
  const [separateTextPrompt, setSeparateTextPrompt] = useState('');
  const { width, height } = useWindowDimensions();
  const styles = useStyles();
  const { recording, URI, errorText, handleStartRecording, handleStopRecording, resetRecording } =
    useAudioRecording();
  const onSubmitSuccess = useCallback(() => {
    resetRecording();
    setSeparateTextPrompt('');
  }, [resetRecording]);
  const { submitActivity, handleSummaryCall } = useSummarySubmission(
    recording,
    URI,
    separateTextPrompt,
    onSubmitSuccess
  );
  useEffect(() => {
  }, [width, height]);
  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#bfaeba', dark: '#60465a' }}
      headerImage={<MaterialIcons size={310} name="settings-voice" style={styles.headerImage} />}
      headerText={<ThemedText type="header">fLoAt</ThemedText>}
    >
      <FloatNotifications />
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Hey! How are you?</ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Something Wrong? Tell me about it.</ThemedText>
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
          <SubmitButton submitActivity={submitActivity} handleSummaryCall={handleSummaryCall} />
        </ThemedView>
      </ThemedView>
    </ParallaxScrollView>
  );
}
