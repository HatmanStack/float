/**
 * DownloadButton - Meditation download component
 * Allows users to download completed meditations for offline playback.
 */

import React, { useState, useCallback } from 'react';
import { Pressable, ActivityIndicator, Alert, Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';
import { Colors } from '@/constants/Colors';
import useStyles from '@/constants/StylesConstants';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

export interface DownloadButtonProps {
  downloadAvailable: boolean;
  onGetDownloadUrl: () => Promise<string>;
  onDownloadStart?: () => void;
  onDownloadComplete?: (localPath: string) => void;
  onDownloadError?: (error: Error) => void;
  fileName?: string;
  disabled?: boolean;
}

type DownloadState = 'idle' | 'fetching_url' | 'downloading' | 'completed' | 'error';

/**
 * Button component to download meditation audio files.
 * Handles URL fetching, file download, and progress tracking.
 */
const DownloadButton: React.FC<DownloadButtonProps> = ({
  downloadAvailable,
  onGetDownloadUrl,
  onDownloadStart,
  onDownloadComplete,
  onDownloadError,
  fileName = 'meditation.mp3',
  disabled = false,
}) => {
  const styles = useStyles();
  const [downloadState, setDownloadState] = useState<DownloadState>('idle');
  const [progress, setProgress] = useState(0);

  const handleDownload = useCallback(async () => {
    if (!downloadAvailable || downloadState === 'downloading' || downloadState === 'fetching_url') {
      return;
    }

    try {
      setDownloadState('fetching_url');
      onDownloadStart?.();

      // Get presigned download URL
      const downloadUrl = await onGetDownloadUrl();

      if (Platform.OS === 'web') {
        // On web, open download URL in new tab
        window.open(downloadUrl, '_blank');
        setDownloadState('completed');
        return;
      }

      // On native, download to local filesystem
      setDownloadState('downloading');
      setProgress(0);

      const localPath = `${FileSystem.documentDirectory}${fileName}`;

      const downloadResumable = FileSystem.createDownloadResumable(
        downloadUrl,
        localPath,
        {},
        (downloadProgress) => {
          const progressPercent = downloadProgress.totalBytesWritten / downloadProgress.totalBytesExpectedToWrite;
          setProgress(Math.round(progressPercent * 100));
        }
      );

      const result = await downloadResumable.downloadAsync();

      if (result?.uri) {
        setDownloadState('completed');
        onDownloadComplete?.(result.uri);

        // Show success message
        Alert.alert(
          'Download Complete',
          'Your meditation has been downloaded successfully.',
          [{ text: 'OK' }]
        );
      } else {
        throw new Error('Download failed - no file URI returned');
      }
    } catch (error) {
      console.error('Download error:', error);
      setDownloadState('error');
      onDownloadError?.(error as Error);

      Alert.alert(
        'Download Failed',
        'Unable to download meditation. Please try again.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Retry', onPress: handleDownload },
        ]
      );
    }
  }, [downloadAvailable, downloadState, onGetDownloadUrl, onDownloadStart, onDownloadComplete, onDownloadError, fileName]);

  const getButtonText = useCallback(() => {
    switch (downloadState) {
      case 'fetching_url':
        return 'Preparing...';
      case 'downloading':
        return `Downloading ${progress}%`;
      case 'completed':
        return 'Downloaded';
      case 'error':
        return 'Retry Download';
      default:
        return 'Download';
    }
  }, [downloadState, progress]);

  // Don't render if download not available
  if (!downloadAvailable) {
    return null;
  }

  const isDisabled = disabled || downloadState === 'fetching_url' || downloadState === 'downloading';

  return (
    <Pressable
      onPress={handleDownload}
      disabled={isDisabled}
      style={({ pressed }) => [
        {
          backgroundColor: isDisabled
            ? Colors['buttonPressed']
            : pressed
            ? Colors['buttonPressed']
            : Colors['buttonUnpressed'],
          opacity: isDisabled ? 0.6 : 1,
        },
        styles.button,
      ]}
      testID="download-button"
    >
      {() => (
        <ThemedView style={{ flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: 'transparent' }}>
          {(downloadState === 'fetching_url' || downloadState === 'downloading') && (
            <ActivityIndicator
              size="small"
              color={Colors['activityIndicator']}
              testID="download-loading-indicator"
            />
          )}
          <ThemedText type="generate">{getButtonText()}</ThemedText>
        </ThemedView>
      )}
    </Pressable>
  );
};

export default DownloadButton;
