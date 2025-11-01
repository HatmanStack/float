// Mock FileSystem BEFORE importing the component
jest.mock('expo-file-system', () => ({
  documentDirectory: 'mock-directory/',
  writeAsStringAsync: jest.fn(() => Promise.resolve()),
  EncodingType: {
    Base64: 'base64',
  },
}));

// Mock fetch BEFORE importing the component
const mockBase64 = 'UklGRgAAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQAC/AAAAABAAEAQAAABAAAAAEAAAB9AAAA';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        body: JSON.stringify({
          base64: mockBase64,
          music_list: ['music1', 'music2'],
        }),
      }),
  })
) as jest.Mock;

// Set environment variable BEFORE importing the component
process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL = 'https://mock-lambda-url.example.com';

import { BackendMeditationCall } from '@/components/BackendMeditationCall';
import { Platform } from 'react-native';

describe('BackendMeditationCall', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset fetch mock with correct response structure
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValueOnce({
        base64: mockBase64,
        music_list: ['music1', 'music2'],
      }),
    });
  });

  it('should successfully invoke Lambda function and return response', async () => {
    const selectedIndexes = [0, 1];

    const resolvedIncidents = [
      {
        sentiment_label: 'Happy',
        intensity: '3',
        speech_to_text: 'Some happy text',
        added_text: 'More happy text',
        summary: 'Summary of happy incident',
      },
      {
        sentiment_label: 'Excited',
        intensity: '4',
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
      user
    );
    expect(webResponse).toEqual({
      responseMeditationURI: 'mock-directory/output.mp3',
      responseMusicList: ['music1', 'music2'],
    });
  });
});
