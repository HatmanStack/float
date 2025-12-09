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

import { BackendMeditationCall, BackendMeditationCallStreaming } from '@/components/BackendMeditationCall';
import * as FileSystem from 'expo-file-system';

const MOCK_LAMBDA_URL = 'https://mock-lambda-url.example.com';
const mockBase64 = 'UklGRgAAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQAC/AAAAABAAEAQAAABAAAAAEAAAB9AAAA';
const mockJobId = 'test-job-id-123';
const mockPlaylistUrl = 'https://s3.example.com/hls/playlist.m3u8?signature=abc123';

afterEach(() => {
  jest.clearAllMocks();
});

describe('BackendMeditationCall', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Setup default successful fetch mock for async job pattern
    // First call: submit job, returns job_id
    // Second call: poll for status, returns completed with result
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
          message: 'Meditation generation started.',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'completed',
          result: {
            base64: mockBase64,
            music_list: ['music1', 'music2'],
          },
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

    expect(payload.input_data).toEqual({
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

    expect(payload.input_data).toEqual({
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

describe('BackendMeditationCallStreaming', () => {
  const defaultIncident = {
    sentiment_label: 'Happy',
    intensity: 3,
    speech_to_text: 'Test',
    added_text: 'Test',
    summary: 'Test',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset FileSystem mock to default behavior
    (FileSystem.writeAsStringAsync as jest.Mock).mockImplementation(() => Promise.resolve());
  });

  it('should return playlist URL when streaming starts', async () => {
    // First call: submit job
    // Second call: poll returns streaming status
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'streaming',
          streaming: {
            playlist_url: mockPlaylistUrl,
            segments_completed: 2,
            segments_total: null,
          },
        }),
      }) as jest.Mock;

    const result = await BackendMeditationCallStreaming(
      [0],
      [defaultIncident],
      ['music1'],
      'testuser',
      MOCK_LAMBDA_URL
    );

    expect(result.jobId).toBe(mockJobId);
    expect(result.playlistUrl).toBe(mockPlaylistUrl);
    expect(result.isStreaming).toBe(true);
    expect(typeof result.waitForCompletion).toBe('function');
    expect(typeof result.getDownloadUrl).toBe('function');
  });

  it('should detect non-streaming jobs (base64 fallback)', async () => {
    // Non-streaming job returns completed with base64
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'completed',
          result: {
            base64: mockBase64,
            music_list: ['music1'],
          },
        }),
      }) as jest.Mock;

    const result = await BackendMeditationCallStreaming(
      [0],
      [defaultIncident],
      ['music1'],
      'testuser',
      MOCK_LAMBDA_URL
    );

    expect(result.isStreaming).toBe(false);
    expect(result.playlistUrl).toBeNull();
    expect(result.responseMeditationURI).toBe('mock-directory/output.mp3');
  });

  it('should call onStatusUpdate during polling', async () => {
    const onStatusUpdate = jest.fn();

    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'processing',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'streaming',
          streaming: {
            playlist_url: mockPlaylistUrl,
            segments_completed: 1,
            segments_total: null,
          },
        }),
      }) as jest.Mock;

    await BackendMeditationCallStreaming(
      [0],
      [defaultIncident],
      ['music1'],
      'testuser',
      MOCK_LAMBDA_URL,
      onStatusUpdate
    );

    expect(onStatusUpdate).toHaveBeenCalledTimes(2);
    expect(onStatusUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'processing' })
    );
    expect(onStatusUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'streaming' })
    );
  });

  it('should waitForCompletion until job completes', async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'streaming',
          streaming: {
            playlist_url: mockPlaylistUrl,
            segments_completed: 5,
            segments_total: 36,
          },
        }),
      })
      // Continuation polling for waitForCompletion
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'completed',
          streaming: {
            playlist_url: mockPlaylistUrl,
            segments_completed: 36,
            segments_total: 36,
          },
          download: {
            available: true,
          },
        }),
      }) as jest.Mock;

    const result = await BackendMeditationCallStreaming(
      [0],
      [defaultIncident],
      ['music1'],
      'testuser',
      MOCK_LAMBDA_URL
    );

    const finalResult = await result.waitForCompletion();

    expect(finalResult.isComplete).toBe(true);
    expect(finalResult.downloadAvailable).toBe(true);
    expect(finalResult.segmentsCompleted).toBe(36);
  });

  it('should getDownloadUrl after completion', async () => {
    const mockDownloadUrl = 'https://s3.example.com/downloads/meditation.mp3?signature=xyz';

    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'completed',
          streaming: {
            playlist_url: mockPlaylistUrl,
            segments_completed: 36,
            segments_total: 36,
          },
          download: { available: true },
        }),
      })
      // Download endpoint call
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          download_url: mockDownloadUrl,
          expires_in: 3600,
        }),
      }) as jest.Mock;

    const result = await BackendMeditationCallStreaming(
      [0],
      [defaultIncident],
      ['music1'],
      'testuser',
      MOCK_LAMBDA_URL
    );

    const downloadUrl = await result.getDownloadUrl();

    expect(downloadUrl).toBe(mockDownloadUrl);
    // Verify download endpoint was called
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/job/test-job-id-123/download'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('should handle failed jobs', async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'failed',
          error: 'Audio generation failed',
        }),
      }) as jest.Mock;

    await expect(
      BackendMeditationCallStreaming(
        [0],
        [defaultIncident],
        ['music1'],
        'testuser',
        MOCK_LAMBDA_URL
      )
    ).rejects.toThrow('Audio generation failed');
  });

  it('should handle structured error messages', async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'pending',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          job_id: mockJobId,
          status: 'failed',
          error: {
            code: 'GENERATION_FAILED',
            message: 'Audio generation failed after 3 attempts',
            retriable: false,
          },
        }),
      }) as jest.Mock;

    await expect(
      BackendMeditationCallStreaming(
        [0],
        [defaultIncident],
        ['music1'],
        'testuser',
        MOCK_LAMBDA_URL
      )
    ).rejects.toThrow('Audio generation failed after 3 attempts');
  });
});
