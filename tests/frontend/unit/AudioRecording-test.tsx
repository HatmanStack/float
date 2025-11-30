// Mock expo-av
const mockRecording = {
  stopAndUnloadAsync: jest.fn(),
  getURI: jest.fn(),
};

jest.mock('expo-av', () => ({
  Audio: {
    requestPermissionsAsync: jest.fn(),
    Recording: {
      createAsync: jest.fn(),
    },
  },
}));

// Mock expo-file-system
jest.mock('expo-file-system', () => ({
  readAsStringAsync: jest.fn(),
  deleteAsync: jest.fn(),
  EncodingType: {
    Base64: 'base64',
  },
}));

// Mock Platform
jest.mock('react-native', () => ({
  Platform: {
    OS: 'ios',
  },
}));

import { StartRecording, StopRecording } from '@/components/AudioRecording';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

describe('AudioRecording', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRecording.stopAndUnloadAsync.mockResolvedValue(undefined);
    mockRecording.getURI.mockReturnValue('file://test-recording.m4a');
  });

  describe('StartRecording', () => {
    it('should request microphone permissions', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
      (Audio.Recording.createAsync as jest.Mock).mockResolvedValue({ recording: mockRecording });

      await StartRecording();

      expect(Audio.requestPermissionsAsync).toHaveBeenCalled();
    });

    it('should create recording when permission is granted', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
      (Audio.Recording.createAsync as jest.Mock).mockResolvedValue({ recording: mockRecording });

      const result = await StartRecording();

      expect(Audio.Recording.createAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          isMeteringEnabled: true,
        })
      );
      expect(result).toBe(mockRecording);
    });

    it('should return null when permission is denied', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'denied' });

      const result = await StartRecording();

      expect(Audio.Recording.createAsync).not.toHaveBeenCalled();
      expect(result).toBeUndefined();
    });

    it('should configure audio settings for iOS', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
      (Audio.Recording.createAsync as jest.Mock).mockResolvedValue({ recording: mockRecording });

      await StartRecording();

      expect(Audio.Recording.createAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          ios: expect.objectContaining({
            extension: '.wav',
            audioQuality: 'high',
            sampleRate: 44100,
            numberOfChannels: 2,
            bitRate: 128000,
          }),
        })
      );
    });

    it('should configure audio settings for Android', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
      (Audio.Recording.createAsync as jest.Mock).mockResolvedValue({ recording: mockRecording });

      await StartRecording();

      expect(Audio.Recording.createAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          android: expect.objectContaining({
            extension: '.m4a',
            outputFormat: 'mpeg4',
            audioEncoder: 'aac',
            sampleRate: 44100,
            numberOfChannels: 2,
            bitRate: 128000,
          }),
        })
      );
    });

    it('should handle recording creation errors', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
      (Audio.Recording.createAsync as jest.Mock).mockRejectedValue(new Error('Failed to create recording'));

      const result = await StartRecording();

      expect(result).toBeNull();
    });

    it('should handle permission request errors', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockRejectedValue(new Error('Permission error'));

      const result = await StartRecording();

      expect(result).toBeNull();
    });
  });

  describe('StopRecording', () => {
    it('should stop recording and return base64 data', async () => {
      const base64Data = 'mockBase64Data==';
      (FileSystem.readAsStringAsync as jest.Mock).mockResolvedValue(base64Data);

      const result = await StopRecording(mockRecording as any);

      expect(mockRecording.stopAndUnloadAsync).toHaveBeenCalled();
      expect(mockRecording.getURI).toHaveBeenCalled();
      expect(FileSystem.readAsStringAsync).toHaveBeenCalledWith(
        'file://test-recording.m4a',
        { encoding: 'base64' }
      );
      expect(result).toBe(base64Data);
    });

    it('should delete recording file after reading on mobile', async () => {
      const base64Data = 'mockBase64Data==';
      (FileSystem.readAsStringAsync as jest.Mock).mockResolvedValue(base64Data);

      await StopRecording(mockRecording as any);

      expect(FileSystem.deleteAsync).toHaveBeenCalledWith('file://test-recording.m4a');
    });

    it('should handle missing recording URI', async () => {
      mockRecording.getURI.mockReturnValue(null);

      const result = await StopRecording(mockRecording as any);

      expect(result).toBeNull();
    });

    it('should handle null recording object', async () => {
      const result = await StopRecording(null as any);

      expect(result).toBeNull();
    });

    it('should handle file read errors', async () => {
      (FileSystem.readAsStringAsync as jest.Mock).mockRejectedValue(new Error('File read failed'));

      const result = await StopRecording(mockRecording as any);

      expect(result).toBeNull();
    });

    it('should handle stop and unload errors', async () => {
      mockRecording.stopAndUnloadAsync.mockRejectedValue(new Error('Stop failed'));

      const result = await StopRecording(mockRecording as any);

      expect(result).toBeNull();
    });
  });
});
