import { Audio } from 'expo-av';
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Pressable, ActivityIndicator, View, StyleSheet } from 'react-native';
import { Colors } from '@/constants/Colors';
import useStyles from '@/constants/StylesConstants';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { HLSPlayer, HLSPlayerRef } from '@/components/HLSPlayer';

/**
 * Duration options for meditation
 */
const DURATION_OPTIONS = [
  { value: 3, label: '3m' },
  { value: 5, label: '5m' },
  { value: 10, label: '10m' },
  { value: 15, label: '15m' },
  { value: 20, label: '20m' },
];

/**
 * Props for MeditationControls component
 */
interface MeditationControlsProps {
  isCalling: boolean;
  meditationURI: string;
  setMeditationURI: (uri: string) => void;
  handleMeditationCall: (durationMinutes: number) => void;
  // HLS streaming props
  playlistUrl?: string | null;
  isStreaming?: boolean;
  onStreamComplete?: () => void;
  onStreamError?: (error: Error) => void;
  // Callback when playback ends (to reset UI to Generate button)
  onPlaybackEnd?: () => void;
}

/**
 * Custom hook for audio playback logic (base64/file mode)
 */
function useAudioPlayback(meditationURI: string, setMeditationURI: (uri: string) => void) {
  const [isPausing, setisPausing] = useState(false);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
    };
  }, []);

  const handlePlayMeditation = useCallback(async () => {
    try {
      let uri = meditationURI;
      if (uri.startsWith('blob:')) {
        // Revoke previous blob URL if any
        if (blobUrlRef.current) {
          URL.revokeObjectURL(blobUrlRef.current);
        }
        const response = await fetch(uri);
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        blobUrlRef.current = blobUrl;
        uri = blobUrl;
      }

      if (sound) {
        if (isPausing) {
          await sound.pauseAsync();
          setisPausing(false);
        } else {
          await sound.playAsync();
          setisPausing(true);
        }
      } else {
        const { sound: newSound } = await Audio.Sound.createAsync({ uri });
        setSound(newSound);
        newSound.setOnPlaybackStatusUpdate(async (status) => {
          if ('didJustFinish' in status && status.didJustFinish) {
            try {
              await newSound.unloadAsync();
            } catch (error) {
              console.error('Error unloading audio:', error);
            }
            // Revoke blob URL when playback finishes
            if (blobUrlRef.current) {
              URL.revokeObjectURL(blobUrlRef.current);
              blobUrlRef.current = null;
            }
            setisPausing(false);
            setSound(null);
            setMeditationURI('');
          }
        });
        await newSound.playAsync();
        setisPausing(true);
      }
    } catch (error) {
      console.error('Error handling the audio file:', error);
    }
  }, [meditationURI, sound, isPausing, setMeditationURI]);

  return {
    isPausing,
    handlePlayMeditation,
  };
}

/**
 * Meditation controls component for playing/pausing meditation audio
 * Supports both legacy base64 mode and HLS streaming mode
 */
const MeditationControls: React.FC<MeditationControlsProps> = ({
  isCalling,
  meditationURI,
  setMeditationURI,
  handleMeditationCall,
  playlistUrl,
  isStreaming = false,
  onStreamComplete,
  onStreamError,
  onPlaybackEnd,
}: MeditationControlsProps): React.JSX.Element => {
  const styles = useStyles();
  const { isPausing, handlePlayMeditation } = useAudioPlayback(meditationURI, setMeditationURI);

  // Duration selector state (must be before any early returns)
  const [selectedDuration, setSelectedDuration] = useState(5);

  // HLS player state
  const hlsPlayerRef = useRef<HLSPlayerRef>(null);
  const [isHLSPlaying, setIsHLSPlaying] = useState(false);
  const [hlsError, setHlsError] = useState<Error | null>(null);

  // HLS playback controls
  const handleHLSPlay = useCallback(() => {
    setIsHLSPlaying(prev => {
      if (prev) {
        hlsPlayerRef.current?.pause();
        return false;
      } else {
        hlsPlayerRef.current?.play();
        return true;
      }
    });
  }, []);

  // HLS event handlers
  const handlePlaybackStart = useCallback(() => {
    setIsHLSPlaying(true);
    setHlsError(null);
  }, []);

  const handlePlaybackPause = useCallback(() => {
    setIsHLSPlaying(false);
  }, []);

  const handlePlaybackComplete = useCallback(() => {
    setIsHLSPlaying(false);
    // Parent will reset playlistUrl via onPlaybackEnd callback
    onPlaybackEnd?.();
  }, [onPlaybackEnd]);

  const handleHLSStreamComplete = useCallback(() => {
    // Stream generation complete (all segments uploaded)
    onStreamComplete?.();
  }, [onStreamComplete]);

  const handleHLSError = useCallback((error: Error) => {
    setHlsError(error);
    setIsHLSPlaying(false);
    onStreamError?.(error);
  }, [onStreamError]);

  // Determine which mode we're in
  const useStreamingMode = isStreaming && playlistUrl;

  // Show loading indicator while generating
  if (isCalling) {
    return (
      <ThemedView style={{ padding: 50 }}>
        <ActivityIndicator
          size="large"
          color={Colors['activityIndicator']}
          testID="activity-indicator"
        />
      </ThemedView>
    );
  }

  // Streaming mode: HLS player (keep mounted even during error for retry to work)
  // Parent resets playlistUrl via onPlaybackEnd when playback finishes
  if (useStreamingMode) {
    return (
      <ThemedView style={{ padding: 20 }}>
        <HLSPlayer
          ref={hlsPlayerRef}
          playlistUrl={playlistUrl}
          onPlaybackStart={handlePlaybackStart}
          onPlaybackPause={handlePlaybackPause}
          onPlaybackComplete={handlePlaybackComplete}
          onStreamComplete={handleHLSStreamComplete}
          onError={handleHLSError}
          autoPlay={false}
        />
        <View style={localStyles.playbackControls}>
          <View style={localStyles.spacer} />
          {hlsError ? (
            <Pressable
              onPress={() => {
                setHlsError(null);
                hlsPlayerRef.current?.play();
              }}
              style={({ pressed }) => [
                {
                  backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
                },
                styles.button,
              ]}
              testID="retry-button"
            >
              <ThemedText type="generate">Retry</ThemedText>
            </Pressable>
          ) : (
            <Pressable
              onPress={handleHLSPlay}
              style={({ pressed }) => [
                {
                  backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
                },
                styles.button,
              ]}
              testID="hls-play-button"
            >
              {({ pressed }) => (
                <ThemedText type="generate">
                  {isHLSPlaying ? (pressed ? 'PAUSING' : 'Pause') : pressed ? 'MEDITATE!' : 'Play'}
                </ThemedText>
              )}
            </Pressable>
          )}
          <View style={localStyles.newButtonWrapper}>
            <Pressable
              onPress={() => {
                hlsPlayerRef.current?.pause();
                setIsHLSPlaying(false);
                onPlaybackEnd?.();
              }}
              style={({ pressed }) => [
                localStyles.newButton,
                pressed && localStyles.newButtonPressed,
              ]}
              testID="new-meditation-button"
            >
              <ThemedText style={localStyles.newButtonText}>New</ThemedText>
            </Pressable>
          </View>
        </View>
      </ThemedView>
    );
  }

  // Legacy base64 mode: expo-av Audio
  if (meditationURI) {
    return (
      <View style={localStyles.playbackControls}>
        <View style={localStyles.spacer} />
        <Pressable
          onPress={handlePlayMeditation}
          style={({ pressed }) => [
            {
              backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
            },
            styles.button,
          ]}
          testID="legacy-play-button"
        >
          {({ pressed }) => (
            <ThemedText type="generate">
              {isPausing ? (pressed ? 'PAUSING' : 'Pause') : pressed ? 'MEDITATE!' : 'Play'}
            </ThemedText>
          )}
        </Pressable>
        <View style={localStyles.newButtonWrapper}>
          <Pressable
            onPress={() => {
              setMeditationURI('');
            }}
            style={({ pressed }) => [
              localStyles.newButton,
              pressed && localStyles.newButtonPressed,
            ]}
            testID="new-meditation-button-legacy"
          >
            <ThemedText style={localStyles.newButtonText}>New</ThemedText>
          </Pressable>
        </View>
      </View>
    );
  }

  // No content yet: show generate button (centered) with duration selector to the right
  return (
    <View style={localStyles.generateContainer}>
      <View style={localStyles.spacer} />
      <Pressable
        onPress={() => handleMeditationCall(selectedDuration)}
        style={({ pressed }) => [
          {
            backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
          },
          styles.button,
          localStyles.generateButton,
        ]}
        testID="generate-button"
      >
        {({ pressed }) => (
          <ThemedText type="generate">{pressed ? 'GENERATING!' : 'Generate'}</ThemedText>
        )}
      </Pressable>
      <View style={localStyles.durationWrapper}>
        <View style={localStyles.durationSelector}>
          {DURATION_OPTIONS.map((option) => (
            <Pressable
              key={option.value}
              onPress={() => setSelectedDuration(option.value)}
              style={[
                localStyles.durationOption,
                selectedDuration === option.value && localStyles.durationOptionSelected,
              ]}
              testID={`duration-${option.value}`}
            >
              <ThemedText
                style={[
                  localStyles.durationText,
                  selectedDuration === option.value && localStyles.durationTextSelected,
                ]}
              >
                {option.label}
              </ThemedText>
            </Pressable>
          ))}
        </View>
      </View>
    </View>
  );
};

const localStyles = StyleSheet.create({
  generateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  playbackControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  newButtonWrapper: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  newButton: {
    backgroundColor: Colors['buttonUnpressed'],
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  newButtonPressed: {
    backgroundColor: Colors['buttonPressed'],
  },
  newButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  spacer: {
    flex: 1,
  },
  generateButton: {
    flex: 0,
    minWidth: 140,
  },
  durationWrapper: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  durationSelector: {
    flexDirection: 'row',
    backgroundColor: Colors['buttonUnpressed'],
    borderRadius: 8,
    padding: 4,
  },
  durationOption: {
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 6,
  },
  durationOptionSelected: {
    backgroundColor: Colors['buttonPressed'],
  },
  durationText: {
    fontSize: 14,
    opacity: 0.7,
  },
  durationTextSelected: {
    opacity: 1,
    fontWeight: '600',
  },
});

export default MeditationControls;
