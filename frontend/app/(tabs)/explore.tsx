import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useWindowDimensions, Platform } from 'react-native';
import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import * as Notifications from 'expo-notifications';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { BackendMeditationCallStreaming, StreamingMeditationResponse } from '@/components/BackendMeditationCall';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { useIncident, Incident } from '@/context/IncidentContext';
import { useAuth } from '@/context/AuthContext';
import Guidance from '@/components/ScreenComponents/Guidance';
import IncidentItem from '@/components/ScreenComponents/IncidentItem';
import MeditationControls from '@/components/ScreenComponents/MeditationControls';
import { DownloadButton } from '@/components/DownloadButton';
import useStyles from '@/constants/StylesConstants';

import { GestureHandlerRootView, Swipeable } from 'react-native-gesture-handler';

/**
 * Custom hook for managing incident selection
 */
function useIncidentSelection() {
  const [selectedIndexes, setSelectedIndexes] = useState<number[]>([]);

  const handlePress = useCallback(
    (index: number) => () => {
      setSelectedIndexes((prevIndexes) => {
        if (prevIndexes.includes(index)) {
          return prevIndexes.filter((i) => i !== index);
        }
        if (prevIndexes.length < 4) {
          return [...prevIndexes, index];
        }
        return prevIndexes;
      });
    },
    []
  );

  return {
    selectedIndexes,
    handlePress,
  };
}

/**
 * Custom hook for managing collapsible state
 */
function useCollapsibleState() {
  const [openIndexes, setOpenIndexes] = useState<Record<number, boolean>>({});

  const toggleCollapsible = useCallback((index: number) => {
    setOpenIndexes((prev) => ({ ...prev, [index]: !prev[index] }));
  }, []);

  return {
    openIndexes,
    toggleCollapsible,
  };
}

/**
 * Custom hook for meditation functionality with streaming support
 */
function useMeditation(selectedIndexes: number[], incidentList: Incident[], musicList: string[]) {
  const [meditationURI, setMeditationURI] = useState('');
  const [isCalling, setIsCalling] = useState(false);
  const { setMusicList } = useIncident();
  const { user } = useAuth();

  // Streaming state
  const [playlistUrl, setPlaylistUrl] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingResponse, setStreamingResponse] = useState<StreamingMeditationResponse | null>(null);
  const [downloadAvailable, setDownloadAvailable] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (isCalling) {
        try {
          const response = await BackendMeditationCallStreaming(
            selectedIndexes,
            incidentList,
            musicList,
            user?.id ?? '',
            undefined, // Use default Lambda URL
            (status) => {
              // Handle status updates during polling
              if (status.streaming?.playlist_url) {
                setPlaylistUrl(status.streaming.playlist_url);
                setIsStreaming(true);
              }
              if (status.download?.available) {
                setDownloadAvailable(true);
              }
            }
          );

          // Store response for download functionality
          setStreamingResponse(response);

          if (response.isStreaming) {
            // Streaming mode: playlist URL already set via callback
            setPlaylistUrl(response.playlistUrl);
            setIsStreaming(true);
            // Update music list if available
            if (response.responseMusicList?.length) {
              setMusicList(response.responseMusicList);
            }
          } else {
            // Legacy base64 mode
            setMeditationURI(response.responseMeditationURI ?? '');
            setMusicList(response.responseMusicList);
            setIsStreaming(false);
          }

          // Check if download is already available
          try {
            const completionResult = await response.waitForCompletion();
            if (completionResult.downloadAvailable) {
              setDownloadAvailable(true);
            }
          } catch (err) {
            // Silent fail - download might not be available yet
            console.debug('Completion check error:', err);
          }
        } catch (error) {
          console.error('Error fetching data:', error);
        } finally {
          setIsCalling(false);
        }
      }
    };

    fetchData();
  }, [isCalling, selectedIndexes, incidentList, musicList, user?.id, setMusicList]);

  const handleMeditationCall = useCallback(() => {
    if (selectedIndexes.length === 0) {
      return;
    }
    // Reset state for new meditation
    setMeditationURI('');
    setPlaylistUrl(null);
    setIsStreaming(false);
    setDownloadAvailable(false);
    setStreamingResponse(null);
    setIsCalling(true);
  }, [selectedIndexes]);

  const handleStreamComplete = useCallback(() => {
    // Stream has finished generating
    setDownloadAvailable(true);
  }, []);

  const handleStreamError = useCallback((error: Error) => {
    console.error('Stream error:', error);
    // Optionally fall back to non-streaming mode or show error UI
  }, []);

  const getDownloadUrl = useCallback(async (): Promise<string> => {
    if (!streamingResponse) {
      throw new Error('No streaming response available');
    }
    return streamingResponse.getDownloadUrl();
  }, [streamingResponse]);

  return {
    meditationURI,
    setMeditationURI,
    isCalling,
    handleMeditationCall,
    // Streaming props
    playlistUrl,
    isStreaming,
    onStreamComplete: handleStreamComplete,
    onStreamError: handleStreamError,
    // Download props
    downloadAvailable,
    getDownloadUrl,
  };
}

/**
 * Custom hook for incident deletion
 */
function useIncidentDeletion() {
  const [asyncDeleteIncident, setAsyncDeleteIncident] = useState<number | null>(null);
  const { incidentList, setIncidentList } = useIncident();

  const cancelScheduledNotification = useCallback(async (notificationId: string) => {
    await Notifications.cancelScheduledNotificationAsync(notificationId);
  }, []);

  useEffect(() => {
    if (asyncDeleteIncident !== null) {
      setIncidentList((prevIncidents) => prevIncidents.filter((_, i) => i !== asyncDeleteIncident));

      if (Platform.OS !== 'web' && incidentList[asyncDeleteIncident]?.notificationId) {
        cancelScheduledNotification(
          (incidentList[asyncDeleteIncident].notificationId ?? '') as string
        );
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
      setAsyncDeleteIncident(null);
    }
  }, [asyncDeleteIncident, incidentList, setIncidentList, cancelScheduledNotification]);

  const handleDeleteIncident = useCallback((index: number) => {
    setAsyncDeleteIncident(index);
  }, []);

  return {
    handleDeleteIncident,
    setAsyncDeleteIncident,
  };
}

/**
 * Explore/Meditate tab screen component
 */
export default function TabTwoScreen(): React.ReactNode {
  const { incidentList, colorChangeArrayOfArrays, musicList } = useIncident();
  const [renderKey, setRenderKey] = useState(0);
  const { width, height } = useWindowDimensions();
  const styles = useStyles();

  const { selectedIndexes, handlePress } = useIncidentSelection();
  const { openIndexes, toggleCollapsible } = useCollapsibleState();
  const { handleDeleteIncident, setAsyncDeleteIncident } = useIncidentDeletion();
  const {
    meditationURI,
    setMeditationURI,
    isCalling,
    handleMeditationCall,
    playlistUrl,
    isStreaming,
    onStreamComplete,
    onStreamError,
    downloadAvailable,
    getDownloadUrl,
  } = useMeditation(selectedIndexes, incidentList, musicList);

  useEffect(() => {
    // This effect is intentionally empty to track width/height changes
  }, [width, height]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    setRenderKey((prevKey) => prevKey + 1);
  }, [colorChangeArrayOfArrays]);

  const renderRightActions = useCallback(
    (index: number) => {
      return (
        <ThemedView style={{ justifyContent: 'center' }}>
          <ThemedText type="subtitle" onPress={() => setAsyncDeleteIncident(index)}>
            Delete
          </ThemedText>
        </ThemedView>
      );
    },
    [setAsyncDeleteIncident]
  );

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ParallaxScrollView
        headerBackgroundColor={{ light: '#bfaeba', dark: '#60465a' }}
        headerImage={
          <MaterialIcons size={310} name="self-improvement" style={styles.headerImage} />
        }
        headerText={<ThemedText type="header">fLoAt</ThemedText>}
      >
        <ThemedView style={styles.titleContainer}>
          <ThemedText type="title">Discovery</ThemedText>
        </ThemedView>
        <Guidance />
        {incidentList.map((incident, index) => {
          if (!incident) {
            handleDeleteIncident(index);
            return null;
          }

          const timestamp = new Date(incident.timestamp).toLocaleString();
          const uniqueKey = timestamp + renderKey;
          return (
            <Swipeable
              key={uniqueKey + 'swipeable'}
              renderRightActions={() => renderRightActions(index)}
            >
              <IncidentItem
                key={uniqueKey}
                renderKey={uniqueKey}
                incident={incident}
                index={index}
                selectedIndexes={selectedIndexes}
                handlePress={handlePress}
                isOpen={!!openIndexes[index]}
                toggleCollapsible={() => toggleCollapsible(index)}
              />
            </Swipeable>
          );
        })}
        <MeditationControls
          isCalling={isCalling}
          meditationURI={meditationURI}
          setMeditationURI={setMeditationURI}
          handleMeditationCall={handleMeditationCall}
          playlistUrl={playlistUrl}
          isStreaming={isStreaming}
          onStreamComplete={onStreamComplete}
          onStreamError={onStreamError}
        />
        <DownloadButton
          downloadAvailable={downloadAvailable}
          onGetDownloadUrl={getDownloadUrl}
          fileName="float-meditation.mp3"
        />
      </ParallaxScrollView>
    </GestureHandlerRootView>
  );
}
