import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

export async function StartRecording () {
    try {
      // Request permissions if needed
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        console.error('Permission to access microphone is required!');
        return;
      }

      // Create a new recording instance
      const { recording } = await Audio.Recording.createAsync(
        Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
      );
      console.log('Recording started');
      return recording;
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
    return null;
  };

export async function StopRecording (recording) {
    try {
      if (recording) {
        await recording.stopAndUnloadAsync();
        const uri = recording.getURI();
        console.log('Recording stopped and stored at:', uri);
        const base64_file = await FileSystem.readAsStringAsync(uri, {
          encoding: FileSystem.EncodingType.Base64,
        });
        return base64_file;
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
    }
    return null;
  };