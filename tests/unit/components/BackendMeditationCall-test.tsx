// Mock FileSystem BEFORE importing the component
jest.mock('expo-file-system', () => ({
  documentDirectory: 'mock-directory/',
  writeAsStringAsync: jest.fn(() => Promise.resolve()),
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

import { BackendMeditationCall } from "@/frontend/components/BackendMeditationCall';
import * as FileSystem from 'expo-file-system';

const MOCK_LAMBDA_URL = 'https://mock-lambda-url.example.com';
const mockBase64 = 'UklGRgAAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQAC/AAAAABAAEAQAAABAAAAAEAAAB9AAAA';

afterEach(() => {
  jest.clearAllMocks();
});

describe('BackendMeditationCall', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Setup default successful fetch mock
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        base64: mockBase64,
        music_list: ['music1', 'music2'],
      }),
    }) as jest.Mock;
  });

  it('should successfully invoke Lambda function and return response', async () => {
    const selectedIndexes = [0, 1];
    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: 3,
        speech_to_text: 'Some happy text',
        added_text: 'More happy text',
        summary: 'Summary of happy incident',
      },
      {
        sentiment_label: 'Excited',
        intensity: 4,
        speech_to_text: 'Some excited text',
        added_text: 'More excited text',
        summary: 'Summary of excitement',
      },
    ];
    const musicList = ['music1', 'music2'];
    const user = 'testuser';

    const webResponse = await BackendMeditationCall(
      selectedIndexes,
      resolvedIncidents,
      musicList,
      user,
      MOCK_LAMBDA_URL
    );

    expect(webResponse).toEqual({
      responseMeditationURI: 'mock-directory/output.mp3',
      responseMusicList: ['music1', 'music2'],
    });
    expect(FileSystem.writeAsStringAsync).toHaveBeenCalledWith(
      'mock-directory/output.mp3',
      mockBase64,
      { encoding: 'base64' }
    );
  });

  it('should handle API errors gracefully', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: jest.fn().mockResolvedValue('Internal Server Error'),
    }) as jest.Mock;

    const selectedIndexes = [0];
    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: 3,
        speech_to_text: 'Test',
        added_text: 'Test',
        summary: 'Test',
      },
    ];
    const musicList = ['music1'];
    const user = 'testuser';

    await expect(
      BackendMeditationCall(selectedIndexes, resolvedIncidents, musicList, user, MOCK_LAMBDA_URL)
    ).rejects.toThrow('Meditation request failed');
  });

  it('should transform incident data correctly', async () => {
    const selectedIndexes = [0, 2]; // Skip index 1
    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: 3,
        speech_to_text: 'Text 1',
        added_text: 'Added 1',
        summary: 'Summary 1',
      },
      {
        sentiment_label: 'Sad',
        intensity: 2,
        speech_to_text: 'Text 2',
        added_text: 'Added 2',
        summary: 'Summary 2',
      },
      {
        sentiment_label: 'Calm',
        intensity: 1,
        speech_to_text: 'Text 3',
        added_text: 'Added 3',
        summary: 'Summary 3',
      },
    ];
    const musicList = ['music1'];
    const user = 'testuser';

    await BackendMeditationCall(selectedIndexes, resolvedIncidents, musicList, user, MOCK_LAMBDA_URL);

    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const payload = JSON.parse(callArgs[1].body);

    expect(payload.transformed_dict).toEqual({
      sentiment_label: ['Happy', 'Calm'],
      intensity: [3, 1],
      speech_to_text: ['Text 1', 'Text 3'],
      added_text: ['Added 1', 'Added 3'],
      summary: ['Summary 1', 'Summary 3'],
    });
  });

  it('should save audio file with correct encoding', async () => {
    const selectedIndexes = [0];
    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: 3,
        speech_to_text: 'Test',
        added_text: 'Test',
        summary: 'Test',
      },
    ];
    const musicList = ['music1'];
    const user = 'testuser';

    await BackendMeditationCall(selectedIndexes, resolvedIncidents, musicList, user, MOCK_LAMBDA_URL);

    expect(FileSystem.writeAsStringAsync).toHaveBeenCalledWith(
      'mock-directory/output.mp3',
      mockBase64,
      { encoding: 'base64' }
    );
  });

  it('should include music list in payload', async () => {
    const selectedIndexes = [0];
    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: 3,
        speech_to_text: 'Test',
        added_text: 'Test',
        summary: 'Test',
      },
    ];
    const musicList = ['track1', 'track2', 'track3'];
    const user = 'testuser';

    await BackendMeditationCall(selectedIndexes, resolvedIncidents, musicList, user, MOCK_LAMBDA_URL);

    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const payload = JSON.parse(callArgs[1].body);

    expect(payload.music_list).toEqual(['track1', 'track2', 'track3']);
  });

  it('should handle empty incident selection', async () => {
    const selectedIndexes: number[] = [];
    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: 3,
        speech_to_text: 'Test',
        added_text: 'Test',
        summary: 'Test',
      },
    ];
    const musicList = ['music1'];
    const user = 'testuser';

    await BackendMeditationCall(selectedIndexes, resolvedIncidents, musicList, user, MOCK_LAMBDA_URL);

    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const payload = JSON.parse(callArgs[1].body);

    expect(payload.transformed_dict).toEqual({
      sentiment_label: [],
      intensity: [],
      speech_to_text: [],
      added_text: [],
      summary: [],
    });
  });

  it('should handle file write errors', async () => {
    (FileSystem.writeAsStringAsync as jest.Mock).mockRejectedValue(new Error('File write failed'));

    const selectedIndexes = [0];
    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: 3,
        speech_to_text: 'Test',
        added_text: 'Test',
        summary: 'Test',
      },
    ];
    const musicList = ['music1'];
    const user = 'testuser';

    await expect(
      BackendMeditationCall(selectedIndexes, resolvedIncidents, musicList, user, MOCK_LAMBDA_URL)
    ).rejects.toThrow('File write failed');
  });
});
