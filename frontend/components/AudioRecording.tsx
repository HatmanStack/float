import { Audio } from "expo-av";
import { Platform } from "react-native";
import * as FileSystem from "expo-file-system";
export async function StartRecording() {
  try {
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== 'granted') {
      console.error('Permission to access microphone is required!');
      return;
    }
    const { recording } = await Audio.Recording.createAsync({
      isMeteringEnabled: true,
      android: {
        extension: '.m4a' as any,
        outputFormat: 'mpeg4' as any,
        audioEncoder: 'aac' as any,
        sampleRate: 44100,
        numberOfChannels: 2,
        bitRate: 128000,
      },
      ios: {
        extension: '.wav' as any,
        audioQuality: 'high' as any,
        sampleRate: 44100,
        numberOfChannels: 2,
        bitRate: 128000,
        linearPCMIsFloat: false,
      },
      web: {} as any,
    });
    console.log('Recording started');
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
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      if (!uri) {
        throw new Error('Failed to get recording URI - recording may not have been finalized');
      }
      let base64_file;
      if (Platform.OS === 'web') {
        const response = await fetch(uri);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const blob = await response.blob();
        base64_file = await convertBlobToBase64(blob);
      } else {
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
