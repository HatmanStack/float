import { BackendSummaryCall } from '@/components/BackendSummaryCall';

// Mock AWS Lambda invoke function
beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
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

// Mock Notifications for non-web environments
jest.mock('expo-notifications', () => ({
  scheduleNotificationAsync: jest.fn(() => Promise.resolve('mocked-notification-id')),
}));

describe('BackendSummaryCall', () => {
  it('should successfully invoke Lambda function and return response', async () => {
    const recordingURI = 'NotAvailable';
    const separateTextPrompt = 'This is a test prompt.';
    const user = 'testuser';

    const response = await BackendSummaryCall(recordingURI, separateTextPrompt, user);

    expect(response).toEqual({
      sentiment_label: 'Happy',
      intensity: '3',
      summary: 'This is a mocked summary.',
      // ... other mocked response properties
      notification_id: 'mocked-notification-id', // From mocked scheduleNotificationAsync
      timestamp: expect.any(String), // Check if it's a string
      color_key: 0,
    });
  });

  // Add more tests to cover error handling, different inputs, etc.
  it('should handle errors gracefully', async () => {
    const recordingURI = 'mocked-recording-uri';
    const separateTextPrompt = 'This is a test prompt.';
    const user = 'testuser';

    // Mock an error during Lambda invocation
    (AWS.Lambda as jest.Mock).mockImplementationOnce(() => ({
      invoke: jest.fn((params, callback) => {
        callback(new Error('Mocked Lambda error'), null);
      }),
    }));

    await expect(BackendSummaryCall(recordingURI, separateTextPrompt, user)).rejects.toThrowError(
      'Mocked Lambda error'
    );
  });
});
