import React, { ReactElement } from 'react';
import { render, RenderOptions, waitFor as rtlWaitFor } from '@testing-library/react-native';
import { AuthProvider } from '../../frontend/context/AuthContext';
import { IncidentProvider } from '../../frontend/context/IncidentContext';

/**
 * Integration Test Utilities
 *
 * These utilities are specifically for integration tests that test
 * interactions between components through Context providers.
 *
 * Unlike component tests, integration tests:
 * - Use REAL Context providers (not mocked)
 * - Test state changes across multiple components
 * - Test data flow through Context
 * - Have longer timeouts for async operations
 */

/**
 * Mock user data for integration testing
 */
export const mockAuthenticatedUser = {
  id: 'test-user-123',
  email: 'test@example.com',
  name: 'Test User',
  photo: 'https://example.com/photo.jpg',
};

export const mockGuestUser = {
  id: 'guest',
  name: 'Guest User',
};

/**
 * Mock incident data for integration testing
 */
export const mockIncident = {
  id: 'incident-1',
  timestamp: new Date('2024-01-01T10:00:00.000Z'),
  sentiment_label: 'Happy',
  intensity: 3,
  speech_to_text: 'I feel great today!',
  added_text: 'Additional context',
  summary: 'User is experiencing positive emotions',
  user_summary: 'Feeling happy',
  user_short_summary: 'Happy',
};

export const mockIncidentList = [
  {
    id: 'incident-1',
    timestamp: new Date('2024-01-01T10:00:00.000Z'),
    sentiment_label: 'Happy',
    intensity: 3,
    speech_to_text: 'Happy speech',
    summary: 'Happy summary',
  },
  {
    id: 'incident-2',
    timestamp: new Date('2024-01-01T11:00:00.000Z'),
    sentiment_label: 'Sad',
    intensity: 2,
    speech_to_text: 'Sad speech',
    summary: 'Sad summary',
  },
  {
    id: 'incident-3',
    timestamp: new Date('2024-01-01T12:00:00.000Z'),
    sentiment_label: 'Angry',
    intensity: 4,
    speech_to_text: 'Angry speech',
    summary: 'Angry summary',
  },
];

export const mockMusicList = [
  'meditation-track-1.mp3',
  'meditation-track-2.mp3',
  'meditation-track-3.mp3',
];

/**
 * Integration test render options
 */
interface IntegrationRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Whether to wrap with providers (default: true for both)
  withAuth?: boolean;
  withIncident?: boolean;
  // Initial state for testing - providers manage their own state
  preloadedState?: {
    user?: any;
    incidents?: any[];
    music?: string[];
  };
}

/**
 * Custom render function for integration tests
 *
 * This function wraps components with REAL Context providers.
 * Use this when testing component interactions through Context.
 *
 * @example
 * ```typescript
 * const { getByText } = renderIntegration(<MyComponent />);
 *
 * // Or with preloaded state
 * const { getByText } = renderIntegration(<MyComponent />, {
 *   preloadedState: {
 *     user: mockAuthenticatedUser,
 *     incidents: mockIncidentList,
 *   }
 * });
 * ```
 */
export function renderIntegration(
  ui: ReactElement,
  {
    withAuth = true,
    withIncident = true,
    preloadedState,
    ...renderOptions
  }: IntegrationRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    let wrapped = <>{children}</>;

    // Wrap with IncidentProvider (real provider)
    if (withIncident) {
      wrapped = <IncidentProvider>{wrapped}</IncidentProvider>;
    }

    // Wrap with AuthProvider (real provider)
    if (withAuth) {
      wrapped = <AuthProvider>{wrapped}</AuthProvider>;
    }

    return wrapped;
  }

  const renderResult = render(ui, { wrapper: Wrapper, ...renderOptions });

  return {
    ...renderResult,
    // Helper to re-render with same wrapper
    rerender: (element: ReactElement) =>
      renderResult.rerender(<Wrapper>{element}</Wrapper>),
  };
}

/**
 * Render with only AuthProvider for auth-specific integration tests
 */
export function renderWithAuthContext(
  ui: ReactElement,
  options: IntegrationRenderOptions = {}
) {
  return renderIntegration(ui, { ...options, withAuth: true, withIncident: false });
}

/**
 * Render with only IncidentProvider for incident-specific integration tests
 */
export function renderWithIncidentContext(
  ui: ReactElement,
  options: IntegrationRenderOptions = {}
) {
  return renderIntegration(ui, { ...options, withAuth: false, withIncident: true });
}

/**
 * Render with both providers (same as renderIntegration with defaults)
 */
export function renderWithAllContexts(
  ui: ReactElement,
  options: IntegrationRenderOptions = {}
) {
  return renderIntegration(ui, { ...options, withAuth: true, withIncident: true });
}

/**
 * Wait for async operations with longer timeout for integration tests
 * Integration tests may involve multiple components and async state updates
 */
export async function waitForIntegration<T>(
  callback: () => T | Promise<T>,
  options?: { timeout?: number; interval?: number }
): Promise<T> {
  return rtlWaitFor(callback, {
    timeout: options?.timeout || 3000, // Longer default timeout for integration tests
    interval: options?.interval || 50,
  });
}

/**
 * Mock AsyncStorage for integration tests
 */
export const mockAsyncStorage = {
  store: new Map<string, string>(),

  getItem: jest.fn((key: string) => {
    return Promise.resolve(mockAsyncStorage.store.get(key) || null);
  }),

  setItem: jest.fn((key: string, value: string) => {
    mockAsyncStorage.store.set(key, value);
    return Promise.resolve();
  }),

  removeItem: jest.fn((key: string) => {
    mockAsyncStorage.store.delete(key);
    return Promise.resolve();
  }),

  clear: jest.fn(() => {
    mockAsyncStorage.store.clear();
    return Promise.resolve();
  }),

  getAllKeys: jest.fn(() => {
    return Promise.resolve(Array.from(mockAsyncStorage.store.keys()));
  }),

  multiGet: jest.fn((keys: string[]) => {
    return Promise.resolve(
      keys.map((key) => [key, mockAsyncStorage.store.get(key) || null])
    );
  }),

  multiSet: jest.fn((pairs: [string, string][]) => {
    pairs.forEach(([key, value]) => mockAsyncStorage.store.set(key, value));
    return Promise.resolve();
  }),

  multiRemove: jest.fn((keys: string[]) => {
    keys.forEach((key) => mockAsyncStorage.store.delete(key));
    return Promise.resolve();
  }),

  // Helper to reset the mock store
  reset: () => {
    mockAsyncStorage.store.clear();
    jest.clearAllMocks();
  },
};

/**
 * Mock navigation for integration tests
 */
export const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  reset: jest.fn(),
  setParams: jest.fn(),
  dispatch: jest.fn(),
  isFocused: jest.fn(() => true),
  canGoBack: jest.fn(() => true),
  addListener: jest.fn(),
  removeListener: jest.fn(),
};

/**
 * Mock route for integration tests
 */
export const mockRoute = {
  key: 'test-route',
  name: 'Test',
  params: {},
};

/**
 * Mock fetch with custom response for backend API calls
 */
export function mockFetchSuccess(response: any, status: number = 200) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    status,
    json: jest.fn().mockResolvedValue(response),
    text: jest.fn().mockResolvedValue(JSON.stringify(response)),
  }) as jest.Mock;
}

/**
 * Mock fetch error for testing error handling
 */
export function mockFetchError(errorMessage: string, status: number = 500) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status,
    statusText: errorMessage,
    json: jest.fn().mockRejectedValue(new Error(errorMessage)),
    text: jest.fn().mockResolvedValue(errorMessage),
  }) as jest.Mock;
}

/**
 * Mock network error (no response)
 */
export function mockNetworkError(message: string = 'Network request failed') {
  global.fetch = jest.fn().mockRejectedValue(new Error(message)) as jest.Mock;
}

/**
 * Reset all mocks for integration tests
 */
export function resetAllMocks() {
  jest.clearAllMocks();
  mockAsyncStorage.reset();
  mockNavigation.navigate.mockClear();
  mockNavigation.goBack.mockClear();
  if (global.fetch && jest.isMockFunction(global.fetch)) {
    (global.fetch as jest.Mock).mockClear();
  }
}

/**
 * Integration test timeout constants
 */
export const INTEGRATION_TIMEOUTS = {
  SHORT: 1000,    // Quick state updates
  MEDIUM: 3000,   // API calls, animations
  LONG: 5000,     // Complex operations
};

// Re-export commonly used testing library functions
export {
  waitFor,
  fireEvent,
  screen,
  within,
  act,
} from '@testing-library/react-native';
