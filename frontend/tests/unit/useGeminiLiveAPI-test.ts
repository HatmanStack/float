import { renderHook, act } from '@testing-library/react-native';
import type { TransformedDict } from '@/components/BackendMeditationCall';
import type { QATranscript } from '@/types/api';

// Mock fetch globally
global.fetch = jest.fn();

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  send = jest.fn();
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
    // Store instance for test access
    MockWebSocket.lastInstance = this;
  }

  static lastInstance: MockWebSocket | null = null;

  // Helper to simulate open
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.({} as Event);
  }

  // Helper to simulate message
  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  }

  // Helper to simulate error
  simulateError() {
    this.onerror?.({} as Event);
  }

  // Helper to simulate close
  simulateClose() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({} as CloseEvent);
  }
}

// @ts-expect-error - Replacing global WebSocket with mock
global.WebSocket = MockWebSocket;

// Mock expo-av Audio for playback
jest.mock('expo-av', () => ({
  Audio: {
    Sound: {
      createAsync: jest.fn().mockResolvedValue({
        sound: {
          playAsync: jest.fn().mockResolvedValue({}),
          unloadAsync: jest.fn().mockResolvedValue({}),
        },
      }),
    },
  },
}));

import useGeminiLiveAPI from '@/hooks/useGeminiLiveAPI';

const MOCK_LAMBDA_URL = 'https://mock-lambda.example.com';
const MOCK_WS_URL =
  'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent';
const MOCK_TOKEN = 'mock-ephemeral-token';

// Set environment variable
process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL = MOCK_LAMBDA_URL;

const mockSentimentData: TransformedDict = {
  sentiment_label: ['Anxious'],
  intensity: [4],
  speech_to_text: ['I had a stressful day'],
  added_text: ['Work was overwhelming'],
  summary: ['Workplace stress'],
};

describe('useGeminiLiveAPI', () => {
  let mockOnTranscriptComplete: jest.Mock;
  let mockOnError: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.lastInstance = null;
    mockOnTranscriptComplete = jest.fn();
    mockOnError = jest.fn();

    // Default mock for token fetch
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        token: MOCK_TOKEN,
        endpoint: MOCK_WS_URL,
      }),
    });
  });

  it('should have initial state as idle with empty transcript', () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    expect(result.current.state).toBe('idle');
    expect(result.current.transcript).toEqual([]);
  });

  it('should fetch token when startSession is called', async () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/token'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('should open WebSocket after fetching token', async () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    expect(MockWebSocket.lastInstance).not.toBeNull();
    expect(MockWebSocket.lastInstance!.url).toContain(MOCK_WS_URL);
  });

  it('should transition to connecting then listening on WebSocket open', async () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    expect(result.current.state).toBe('connecting');

    await act(async () => {
      MockWebSocket.lastInstance!.simulateOpen();
    });

    expect(result.current.state).toBe('listening');
  });

  it('should accumulate transcript from assistant messages', async () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await act(async () => {
      MockWebSocket.lastInstance!.simulateOpen();
    });

    await act(async () => {
      MockWebSocket.lastInstance!.simulateMessage({
        serverContent: {
          modelTurn: {
            parts: [{ text: 'How are you feeling about the stress at work?' }],
          },
          turnComplete: true,
        },
      });
    });

    expect(result.current.transcript).toEqual([
      { role: 'assistant', text: 'How are you feeling about the stress at work?' },
    ]);
  });

  it('should end session after max exchanges and call onTranscriptComplete', async () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await act(async () => {
      MockWebSocket.lastInstance!.simulateOpen();
    });

    // Exchange 1: assistant asks
    await act(async () => {
      MockWebSocket.lastInstance!.simulateMessage({
        serverContent: {
          modelTurn: {
            parts: [{ text: 'How are you feeling?' }],
          },
          turnComplete: true,
        },
      });
    });

    // User responds
    await act(async () => {
      result.current.sendTextMessage('I feel stressed');
    });

    // Exchange 2: assistant responds
    await act(async () => {
      MockWebSocket.lastInstance!.simulateMessage({
        serverContent: {
          modelTurn: {
            parts: [{ text: 'Tell me more about what happened.' }],
          },
          turnComplete: true,
        },
      });
    });

    // User responds
    await act(async () => {
      result.current.sendTextMessage('My boss gave harsh feedback');
    });

    // Exchange 3: assistant wraps up (this should trigger auto-end)
    await act(async () => {
      MockWebSocket.lastInstance!.simulateMessage({
        serverContent: {
          modelTurn: {
            parts: [{ text: 'Thank you for sharing. Let me create a meditation for you.' }],
          },
          turnComplete: true,
        },
      });
    });

    expect(result.current.state).toBe('complete');
    expect(mockOnTranscriptComplete).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ role: 'assistant' }),
        expect.objectContaining({ role: 'user' }),
      ])
    );
  });

  it('should close WebSocket when endSession is called', async () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await act(async () => {
      MockWebSocket.lastInstance!.simulateOpen();
    });

    await act(async () => {
      result.current.endSession();
    });

    expect(MockWebSocket.lastInstance!.close).toHaveBeenCalled();
  });

  it('should send text message via WebSocket', async () => {
    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await act(async () => {
      MockWebSocket.lastInstance!.simulateOpen();
    });

    await act(async () => {
      result.current.sendTextMessage('hello');
    });

    expect(MockWebSocket.lastInstance!.send).toHaveBeenCalledWith(expect.stringContaining('hello'));
    expect(result.current.transcript).toContainEqual({ role: 'user', text: 'hello' });
  });

  it('should call onError when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() =>
      useGeminiLiveAPI({
        sentimentData: mockSentimentData,
        onTranscriptComplete: mockOnTranscriptComplete,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    expect(mockOnError).toHaveBeenCalledWith(expect.any(Error));
  });
});
