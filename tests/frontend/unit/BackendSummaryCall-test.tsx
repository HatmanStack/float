// Mock expo-notifications
jest.mock('expo-notifications', () => ({
  scheduleNotificationAsync: jest.fn(() => Promise.resolve('mocked-notification-id')),
}));

// Mock Platform to avoid notification scheduling in tests (set to 'web' to skip notifications)
jest.mock('react-native', () => ({
  Platform: {
    OS: 'web',
  },
}));

import { BackendSummaryCall } from '@/components/BackendSummaryCall';

const MOCK_LAMBDA_URL = 'https://mock-lambda-url.example.com';

afterEach(() => {
  jest.clearAllMocks();
});

describe('BackendSummaryCall', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Setup default successful fetch mock
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        sentiment_label: 'Happy',
        intensity: 3,
        summary: 'This is a mocked summary.',
      }),
    }) as jest.Mock;
  });

  it('should successfully invoke Lambda function and return response', async () => {
    const recordingURI = 'NotAvailable';
    const separateTextPrompt = 'This is a test prompt.';
    const user = 'testuser';

    const response = await BackendSummaryCall(recordingURI, separateTextPrompt, user, MOCK_LAMBDA_URL);

    expect(response).toMatchObject({
      sentiment_label: 'Happy',
      intensity: 3,
      summary: 'This is a mocked summary.',
    });
    expect(response.timestamp).toBeDefined();
    expect(typeof response.timestamp).toBe('string');
    expect(response.color_key).toBe(0);
  });

  it('should handle errors gracefully when fetch fails', async () => {
    const recordingURI = 'mocked-recording-uri';
    const separateTextPrompt = 'This is a test prompt.';
    const user = 'testuser';

    // Mock fetch to return an error response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: jest.fn().mockResolvedValueOnce('Internal Server Error'),
    });

    await expect(BackendSummaryCall(recordingURI, separateTextPrompt, user, MOCK_LAMBDA_URL)).rejects.toThrow(
      'Request to Summary Lambda URL failed with status 500'
    );
  });

  it('should use "NotAvailable" when recording URI is null', async () => {
    const recordingURI = null;
    const separateTextPrompt = 'This is a test prompt.';
    const user = 'testuser';

    await BackendSummaryCall(recordingURI, separateTextPrompt, user, MOCK_LAMBDA_URL);

    expect(global.fetch).toHaveBeenCalledWith(
      MOCK_LAMBDA_URL,
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: expect.stringContaining('"audio":"NotAvailable"'),
      })
    );
  });

  it('should use "NotAvailable" when text prompt is empty', async () => {
    const recordingURI = 'mocked-uri';
    const separateTextPrompt = '';
    const user = 'testuser';

    await BackendSummaryCall(recordingURI, separateTextPrompt, user, MOCK_LAMBDA_URL);

    expect(global.fetch).toHaveBeenCalledWith(
      MOCK_LAMBDA_URL,
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"prompt":"NotAvailable"'),
      })
    );
  });

  it('should include correct payload structure', async () => {
    const recordingURI = 'file://recording.m4a';
    const separateTextPrompt = 'Test prompt';
    const user = 'testuser';

    await BackendSummaryCall(recordingURI, separateTextPrompt, user, MOCK_LAMBDA_URL);

    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const payload = JSON.parse(callArgs[1].body);

    expect(payload).toEqual({
      inference_type: 'summary',
      audio: 'file://recording.m4a',
      prompt: 'Test prompt',
      input_data: 'NotAvailable',
      user_id: 'testuser',
    });
  });

  it('should throw error when invalid URL is provided', async () => {
    const recordingURI = 'file://recording.m4a';
    const separateTextPrompt = 'Test prompt';
    const user = 'testuser';

    await expect(BackendSummaryCall(recordingURI, separateTextPrompt, user, '')).rejects.toThrow(
      'FATAL: LAMBDA_FUNCTION_URL is not set'
    );
  });
});
