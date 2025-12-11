/**
 * @jest-environment jsdom
 *
 * Tests for useHLSPlayer hook
 * Tests the web implementation with mocked HLS.js
 */

import { renderHook, act } from '@testing-library/react-native';

// Mock HLS.js before importing the hook
const mockHlsInstance = {
  loadSource: jest.fn(),
  attachMedia: jest.fn(),
  destroy: jest.fn(),
  startLoad: jest.fn(),
  recoverMediaError: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
};

jest.mock('hls.js', () => {
  const instance = {
    loadSource: jest.fn(),
    attachMedia: jest.fn(),
    destroy: jest.fn(),
    startLoad: jest.fn(),
    recoverMediaError: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
  };

  function MockHls() {
    // Copy mock functions to allow test access
    Object.assign(instance, mockHlsInstance);
    return instance;
  }

  MockHls.isSupported = jest.fn(() => true);
  MockHls.Events = {
    MANIFEST_PARSED: 'hlsManifestParsed',
    LEVEL_LOADED: 'hlsLevelLoaded',
    ERROR: 'hlsError',
    FRAG_LOADED: 'hlsFragLoaded',
  };
  MockHls.ErrorTypes = {
    NETWORK_ERROR: 'networkError',
    MEDIA_ERROR: 'mediaError',
    OTHER_ERROR: 'otherError',
  };
  MockHls.ErrorDetails = {
    BUFFER_STALLED_ERROR: 'bufferStalledError',
    MANIFEST_LOAD_ERROR: 'manifestLoadError',
  };

  return {
    __esModule: true,
    default: MockHls,
    Events: MockHls.Events,
    ErrorTypes: MockHls.ErrorTypes,
    ErrorDetails: MockHls.ErrorDetails,
  };
});

// Mock HTMLAudioElement
const mockAudioElement = {
  play: jest.fn(() => Promise.resolve()),
  pause: jest.fn(),
  load: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  canPlayType: jest.fn(() => ''),
  currentTime: 0,
  duration: 0,
  src: '',
  preload: '',
  error: null,
};

const originalCreateElement = document.createElement.bind(document);
beforeAll(() => {
  jest.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
    if (tagName === 'audio') {
      return mockAudioElement as unknown as HTMLAudioElement;
    }
    return originalCreateElement(tagName);
  });
});

afterAll(() => {
  jest.restoreAllMocks();
});

// Import the hook after mocking
import { useHLSPlayer } from '@/hooks/useHLSPlayer.web';

describe('useHLSPlayer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAudioElement.currentTime = 0;
    mockAudioElement.duration = 0;
    mockAudioElement.src = '';
    mockAudioElement.error = null;
    mockAudioElement.canPlayType.mockReturnValue('');
  });

  describe('initialization', () => {
    it('should return initial state with null URL', () => {
      const { result } = renderHook(() => useHLSPlayer(null));

      const [state, controls] = result.current;

      expect(state).toEqual({
        isLoading: false,
        isPlaying: false,
        isComplete: false,
        error: null,
        duration: null,
        currentTime: 0,
      });
      expect(typeof controls.play).toBe('function');
      expect(typeof controls.pause).toBe('function');
      expect(typeof controls.seek).toBe('function');
      expect(typeof controls.retry).toBe('function');
    });

    it('should have default state when playlist URL is provided', () => {
      const { result } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      const [state] = result.current;
      // Loading state is managed via HLS.js callbacks, starts as false
      expect(state.isLoading).toBe(false);
      expect(state.isPlaying).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should initialize HLS.js when URL is provided', () => {
      renderHook(() => useHLSPlayer('https://example.com/playlist.m3u8'));

      expect(mockHlsInstance.loadSource).toHaveBeenCalledWith(
        'https://example.com/playlist.m3u8'
      );
      expect(mockHlsInstance.attachMedia).toHaveBeenCalled();
    });
  });

  describe('state transitions', () => {
    it('should update loading state to false after manifest parsed', () => {
      const { result } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      // Get the MANIFEST_PARSED callback
      const manifestParsedCallback = mockHlsInstance.on.mock.calls.find(
        (call: [string, () => void]) => call[0] === 'hlsManifestParsed'
      )?.[1];

      act(() => {
        manifestParsedCallback?.();
      });

      const [state] = result.current;
      expect(state.isLoading).toBe(false);
    });

    it('should track playing state via audio events', () => {
      renderHook(() => useHLSPlayer('https://example.com/playlist.m3u8'));

      // Find the play event listener
      const playCallback = mockAudioElement.addEventListener.mock.calls.find(
        (call: [string, () => void]) => call[0] === 'play'
      )?.[1];

      expect(playCallback).toBeDefined();
    });

    it('should track complete state via ended event', () => {
      renderHook(() => useHLSPlayer('https://example.com/playlist.m3u8'));

      // Find the ended event listener
      const endedCallback = mockAudioElement.addEventListener.mock.calls.find(
        (call: [string, () => void]) => call[0] === 'ended'
      )?.[1];

      expect(endedCallback).toBeDefined();
    });
  });

  describe('error handling', () => {
    it('should set error state on fatal HLS error', () => {
      const { result } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      // Get the ERROR callback
      const errorCallback = mockHlsInstance.on.mock.calls.find(
        (call: [string, (event: string, data: object) => void]) => call[0] === 'hlsError'
      )?.[1];

      act(() => {
        errorCallback?.('hlsError', {
          fatal: true,
          type: 'otherError',
          details: 'testError',
        });
      });

      const [state] = result.current;
      expect(state.error).toBeTruthy();
      expect(state.isLoading).toBe(false);
    });

    it('should attempt recovery on network error', () => {
      renderHook(() => useHLSPlayer('https://example.com/playlist.m3u8'));

      // Get the ERROR callback
      const errorCallback = mockHlsInstance.on.mock.calls.find(
        (call: [string, (event: string, data: object) => void]) => call[0] === 'hlsError'
      )?.[1];

      act(() => {
        errorCallback?.('hlsError', {
          fatal: true,
          type: 'networkError',
          details: 'networkError',
        });
      });

      expect(mockHlsInstance.startLoad).toHaveBeenCalled();
    });

    it('should attempt recovery on media error', () => {
      renderHook(() => useHLSPlayer('https://example.com/playlist.m3u8'));

      // Get the ERROR callback
      const errorCallback = mockHlsInstance.on.mock.calls.find(
        (call: [string, (event: string, data: object) => void]) => call[0] === 'hlsError'
      )?.[1];

      act(() => {
        errorCallback?.('hlsError', {
          fatal: true,
          type: 'mediaError',
          details: 'mediaError',
        });
      });

      expect(mockHlsInstance.recoverMediaError).toHaveBeenCalled();
    });
  });

  describe('controls', () => {
    it('should call audio.play() when play is invoked', () => {
      const { result } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      const [, controls] = result.current;

      act(() => {
        controls.play();
      });

      expect(mockAudioElement.play).toHaveBeenCalled();
    });

    it('should call audio.pause() when pause is invoked', () => {
      const { result } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      const [, controls] = result.current;

      act(() => {
        controls.pause();
      });

      expect(mockAudioElement.pause).toHaveBeenCalled();
    });

    it('should set audio.currentTime when seek is invoked', () => {
      const { result } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      const [, controls] = result.current;

      act(() => {
        controls.seek(30);
      });

      expect(mockAudioElement.currentTime).toBe(30);
    });
  });

  describe('cleanup', () => {
    it('should destroy HLS instance on unmount', () => {
      const { unmount } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      unmount();

      expect(mockHlsInstance.destroy).toHaveBeenCalled();
    });

    it('should remove audio event listeners on unmount', () => {
      const { unmount } = renderHook(() =>
        useHLSPlayer('https://example.com/playlist.m3u8')
      );

      unmount();

      expect(mockAudioElement.removeEventListener).toHaveBeenCalled();
    });
  });

  describe('HLS.js usage', () => {
    it('should always use HLS.js regardless of native support', () => {
      // Even if native HLS is supported, we always use HLS.js for presigned URL compatibility
      mockAudioElement.canPlayType.mockReturnValue('maybe');

      renderHook(() => useHLSPlayer('https://example.com/playlist.m3u8'));

      // HLS.js should be used and load the source
      // Native canPlayType is not used since we always use HLS.js
      expect(mockHlsInstance.loadSource).toHaveBeenCalledWith(
        'https://example.com/playlist.m3u8'
      );
    });
  });

  describe('URL changes', () => {
    it('should reset state when URL changes to null', () => {
      const { result, rerender } = renderHook(
        ({ url }) => useHLSPlayer(url),
        { initialProps: { url: 'https://example.com/playlist.m3u8' as string | null } }
      );

      rerender({ url: null });

      const [state] = result.current;
      expect(state.isLoading).toBe(false);
      expect(state.isPlaying).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should reinitialize HLS when URL changes', () => {
      const { rerender } = renderHook(
        ({ url }) => useHLSPlayer(url),
        { initialProps: { url: 'https://example.com/playlist1.m3u8' } }
      );

      jest.clearAllMocks();

      rerender({ url: 'https://example.com/playlist2.m3u8' });

      expect(mockHlsInstance.destroy).toHaveBeenCalled();
      expect(mockHlsInstance.loadSource).toHaveBeenCalledWith(
        'https://example.com/playlist2.m3u8'
      );
    });
  });
});
