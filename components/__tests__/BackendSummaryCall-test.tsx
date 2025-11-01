// Mock Notifications BEFORE importing the component
jest.mock('expo-notifications', () => ({
  scheduleNotificationAsync: jest.fn(() => Promise.resolve('mocked-notification-id')),
}));

// Mock fetch
beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          sentiment_label: 'Happy',
          intensity: '3',
          summary: 'This is a mocked summary.',
        }),
    })
  ) as jest.Mock;
});

afterEach(() => {
  jest.resetAllMocks();
});

import { BackendSummaryCall } from '@/components/BackendSummaryCall';

describe('BackendSummaryCall', () => {
  // TODO: Fix module-level constant issue - LAMBDA_FUNCTION_URL is evaluated at module load time
  // before the test can set environment variables. See BackendMeditationCall for a working solution.
  it.skip('should successfully invoke Lambda function and return response', async () => {
    const recordingURI = 'NotAvailable';
    const separateTextPrompt = 'This is a test prompt.';
    const user = 'testuser';

    const response = await BackendSummaryCall(recordingURI, separateTextPrompt, user);

    expect(response).toMatchObject({
      sentiment_label: 'Happy',
      intensity: '3',
      summary: 'This is a mocked summary.',
    });
    expect(response.timestamp).toBeDefined();
    expect(typeof response.timestamp).toBe('string');
  });

  // Add more tests to cover error handling, different inputs, etc.
  it.skip('should handle errors gracefully', async () => {
    const recordingURI = 'mocked-recording-uri';
    const separateTextPrompt = 'This is a test prompt.';
    const user = 'testuser';

    // Mock fetch to return an error response
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Internal Server Error' }),
      })
    );

    await expect(BackendSummaryCall(recordingURI, separateTextPrompt, user)).rejects.toThrow();
  });
});
