import { Image,Button, TextInput, StyleSheet, ActivityIndicator } from 'react-native';
import React, { useState, useEffect } from 'react';
import { HelloWave } from '@/components/HelloWave';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { StartRecording, StopRecording } from '@/components/AudioRecording';
import { BackendSummaryCall } from '@/components/BackendSummaryCall';
import { useIncident } from '@/context/IncidentContext';

export default function HomeScreen() {
  const [separateTextPrompt, setSeparateTextPrompt] = useState<string | null>(null);
  const [recording, setRecording] = useState(null);
  const [URI, setURI] = useState<string | null>(null);
  const [summaryCall, setSummaryCall] = useState(false);
  const { setIncidentList } = useIncident();

  const handleStartRecording = async () => {
    const recording = await StartRecording();
    setRecording(recording);
  }

  const handleStopRecording = async () => {
    const uri = await StopRecording(recording);
    setURI(uri);
    console.log('Recording stopped and stored at:', uri);
  }

  const handleSummaryCall = async () => {
    setSummaryCall(true);
  }

  useEffect(() => {
    const fetchData = async () => {
        if (summaryCall) {
            if (!recording && !separateTextPrompt) {
                return;
            }
            try {
                let response;
                if (recording) {
                    const base64_file = await StopRecording(recording);
                    response = await BackendSummaryCall(base64_file, separateTextPrompt);
                } else {
                    response = await BackendSummaryCall(URI, separateTextPrompt);
                }
                setIncidentList(prevIncidentList => [response, ...prevIncidentList]);
            } catch (error) {
                console.error('Failed to call summary lambda:', error);
            }
            setSummaryCall(false);
        }
    };

    fetchData();
}, [summaryCall]);


  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#A1CEDC', dark: '#1D3D47' }}
      headerImage={
        <Image
          source={require('@/assets/images/partial-react-logo.png')}
          style={styles.reactLogo}
        />
      }>
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Hey! How are you?</ThemedText>
        <HelloWave />
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Something Wrong? Tell me about it.</ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <Button title="Activate Microphone" onPress={recording ? handleStopRecording : handleStartRecording} />
        {recording && <ThemedText>Recording...</ThemedText>}
        <TextInput
          style={styles.input}
          placeholder="Type your response"
          value={separateTextPrompt}
          onChangeText={setSeparateTextPrompt}
        />
        {summaryCall ? <ActivityIndicator size="large" color="#B58392"  /> : <Button title="Submit" onPress={handleSummaryCall} />}
      </ThemedView>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  stepContainer: {
    gap: 8,
    marginBottom: 8,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
  input: {
    height: 40,
    borderColor: 'gray',
    borderWidth: 1,
    marginTop: 10,
    paddingHorizontal: 10,
  },
});
