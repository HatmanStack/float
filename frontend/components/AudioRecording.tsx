import { Audio } from 'expo-av';
import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';

// Custom recording options for high quality audio
const RECORDING_OPTIONS: Audio.RecordingOptions = {
  isMeteringEnabled: true,
  android: {
    extension: '.m4a',
    outputFormat: Audio.AndroidOutputFormat.MPEG_4,
    audioEncoder: Audio.AndroidAudioEncoder.AAC,
    sampleRate: 44100,
    numberOfChannels: 2,
    bitRate: 128000,
  },
  ios: {
    extension: '.wav',
    audioQuality: Audio.IOSAudioQuality.HIGH,
    sampleRate: 44100,
    numberOfChannels: 2,
    bitRate: 128000,
    linearPCMIsFloat: false,
    linearPCMIsBigEndian: false,
    linearPCMBitDepth: 16,
  },
  web: {
    mimeType: 'audio/webm',
    bitsPerSecond: 128000,
  },
};

export async function StartRecording() {
  try {
    // Request permissions if needed
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== 'granted') {
      console.error('Permission to access microphone is required!');
      return;
    }

    // Create a new recording instance
    const { recording } = await Audio.Recording.createAsync(RECORDING_OPTIONS);
    return recording;
  } catch (error) {
    console.error('Failed to start recording:', error);
  }
  return null;
}

function convertBlobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(((reader.result as string) || '').split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export async function StopRecording(recording: Audio.Recording): Promise<string | null> {
  try {
    if (recording) {
      // Finalize the recording before attempting to get URI
      await recording.stopAndUnloadAsync();

      const uri = recording.getURI();

      if (!uri) {
        throw new Error('Failed to get recording URI - recording may not have been finalized');
      }

      let base64_file;

      if (Platform.OS === 'web') {
        // Web-specific code
        const response = await fetch(uri);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const blob = await response.blob();
        base64_file = await convertBlobToBase64(blob);
      } else {
        // Mobile-specific code
        base64_file = await FileSystem.readAsStringAsync(uri, {
          encoding: FileSystem.EncodingType.Base64,
        });
        await FileSystem.deleteAsync(uri);
      }

      return base64_file;
    }
  } catch (error) {
    console.error('Failed to stop recording:', error);
  }
  return null;
}
