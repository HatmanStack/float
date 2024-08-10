import { Audio } from "expo-av";
import { Platform } from "react-native";
import * as FileSystem from "expo-file-system";

export async function StartRecording() {
  try {
    // Request permissions if needed
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== "granted") {
      console.error("Permission to access microphone is required!");
      return;
    }

    // Create a new recording instance
    const { recording } = await Audio.Recording.createAsync(
      Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
    );
    console.log("Recording started");
    return recording;
  } catch (error) {
    console.error("Failed to start recording:", error);
  }
  return null;
}

function convertBlobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export async function StopRecording(recording) {
  try {
    if (recording) {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();

      let base64_file;

      if (Platform.OS === "web") {
        // Web-specific code
        const response = await fetch(uri);
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        const blob = await response.blob();
        base64_file = await convertBlobToBase64(blob);
      } else {
        // Mobile-specific code
        base64_file = await FileSystem.readAsStringAsync(uri, {
          encoding: FileSystem.EncodingType.Base64,
        });
      }

      return base64_file;
    }
  } catch (error) {
    console.error("Failed to stop recording:", error);
  }
  return null;
}
