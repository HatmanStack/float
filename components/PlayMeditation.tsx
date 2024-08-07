import { Audio } from 'expo-av';

const playMeditation = async (meditationURI, setIsPlaying, setMeditationURI) => {
  try {
    let uri = meditationURI;
    if (uri.startsWith('blob:')) {
      const response = await fetch(uri);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      uri = blobUrl;
    }

    const { sound } = await Audio.Sound.createAsync({ uri });
    sound.setOnPlaybackStatusUpdate(async (status) => {
      if (status.didJustFinish) {
        console.log('Audio file finished playing');
        setIsPlaying(false);
        setMeditationURI('');
      }
    });
    await sound.playAsync();
    console.log('Playing the file:', uri);
  } catch (error) {
    console.error('Error handling the audio file:', error);
  }
};

export default playMeditation;