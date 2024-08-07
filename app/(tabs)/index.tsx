import { Image, TextInput, StyleSheet, ActivityIndicator, Pressable, useColorScheme } from 'react-native';
import React, { useState, useEffect } from 'react';
import { HelloWave } from '@/components/HelloWave';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { StartRecording, StopRecording } from '@/components/AudioRecording';
import { BackendSummaryCall } from '@/components/BackendSummaryCall';
import { useIncident } from '@/context/IncidentContext';
import { Audio } from 'expo-av';
import { Platform } from 'react-native';

export default function HomeScreen() {
  const [separateTextPrompt, setSeparateTextPrompt] = useState('');
  const [recording, setRecording] = useState(null);
  const [URI, setURI] = useState('');
  const [errorText, setErrorText] = useState(false);
  const [summaryCall, setSummaryCall] = useState(false);
  const { setIncidentList } = useIncident();
  const colorScheme = useColorScheme();

  const handleStartRecording = async () => {
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
      setRecording(recording);
      setErrorText(false);
    } catch (error) {
      console.error('Microphone is not available:', error);
      setErrorText(true);
    }
  };

  const handleStopRecording = async () => {
    const uri = await StopRecording(recording);
    setURI(uri);
    setRecording(null);
    console.log('Recording stopped and stored at:', uri);
  }

  const handleSummaryCall = async () => {
    setSummaryCall(true);
  }

  useEffect(() => {
    const fetchData = async () => {
        if (summaryCall) {
            if (!recording && !separateTextPrompt) {
              console.log('Returning early due to null recording and empty separateTextPrompt');
              setSummaryCall(false);
              return;
          }
            try {
                let response;
                if (recording) {
                  const base64_file = await StopRecording(recording);
                  response = BackendSummaryCall(base64_file, separateTextPrompt);
                } else {
                  response = BackendSummaryCall(URI, separateTextPrompt) 
                }
                setSummaryCall(false);
                setErrorText(false);
                setIncidentList(prevList => [response, ...prevList]);
                setRecording(null);
                setURI('');
            } catch (error) {
                setSummaryCall(false);
                console.error('Failed to call summary lambda:', error);
            }
            
        }
    };

    fetchData();
}, [summaryCall]);

const imageSource = colorScheme === 'dark'
    ? require('@/assets/images/self_improvement_white.svg')
    : require('@/assets/images/self_improvement_dark.svg');

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#A1CEDC', dark: '#1D3D47' }}
      headerImage={
        <Image
          source={imageSource}
          style={styles.Logo}
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
        
        <TextInput
          style={styles.input}
          placeholder="Type or Chat"
          value={separateTextPrompt}
          multiline={true}
          textAlignVertical="top"
          onChangeText={setSeparateTextPrompt}
        />
        <ThemedView style={[styles.stepContainer, { flexDirection: 'row', justifyContent: 'space-evenly', margin : 30 }]}>
        <ThemedView style={{flexDirection: 'column'}}>
        <Pressable onPress={recording ? handleStopRecording : handleStartRecording}
        style={({ pressed }) => [
          { backgroundColor: pressed ? "#958DA5" : "#9DA58D" },
          styles.button 
        ]}>{({ pressed }) => (
          <ThemedText type="generate">{recording ? pressed ? "STOP RECORDING": "Stop Recording" : pressed ? "RECORDING!" : "Record Audio"}</ThemedText>
        )}
        </Pressable>
        {errorText && <ThemedText>Microphone is not available</ThemedText>}
        {recording && <ThemedText>Recording...</ThemedText>}
        </ThemedView>
        {summaryCall ? <ActivityIndicator size="large" color="#B58392"  /> : 
        <Pressable onPress={handleSummaryCall}
        style={({ pressed }) => [
          { backgroundColor: pressed ? "#958DA5" : "#9DA58D" },
          styles.button 
        ]}>{({ pressed }) => (
          <ThemedText type="generate">{pressed ? "SUBMITTING!" : "Submit Incident"}</ThemedText>
        )}
        </Pressable>}
        </ThemedView>
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
  Logo: {
    height: 200,
    width: 300,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
  input: {
    height: 200,
    borderColor: 'gray',
    borderWidth: 1,
    marginTop: 10,
    fontSize: 20,
    paddingHorizontal: 10,
    backgroundColor: '#FFFFFF',
  },
  button: {
    padding: 20,
    borderRadius: 20,
    width: 200,
    alignSelf: 'center'
  }
});
