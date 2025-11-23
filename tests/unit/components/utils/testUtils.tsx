import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react-native";
import { AuthProvider } from "@/frontend/context/AuthContext";
import { IncidentProvider } from "@/frontend/context/IncidentContext";

/**
 * Mock user data for testing
 */
export const mockUser = {
  id: 'test-user-123',
  name: 'Test User',
};

export const mockGuestUser = {
  id: 'guest',
  name: 'Guest User',
};

/**
 * Mock incident data for testing
 */
export const mockIncident = {
  sentiment_label: 'Happy',
  intensity: 3,
  speech_to_text: 'Test speech text',
  added_text: 'Test added text',
  summary: 'Test summary',
  notification_id: 'notif-123',
  timestamp: '2024-01-01T00:00:00.000Z',
  color_key: 0,
};

export const mockIncidentList = [
  {
    sentiment_label: 'Happy',
    intensity: 3,
    speech_to_text: 'Happy speech',
    added_text: 'Happy added',
    summary: 'Happy summary',
    timestamp: '2024-01-01T10:00:00.000Z',
    color_key: 0,
  },
  {
    sentiment_label: 'Sad',
    intensity: 2,
    speech_to_text: 'Sad speech',
    added_text: 'Sad added',
    summary: 'Sad summary',
    timestamp: '2024-01-01T11:00:00.000Z',
    color_key: 1,
  },
  {
    sentiment_label: 'Angry',
    intensity: 4,
    speech_to_text: 'Angry speech',
    added_text: 'Angry added',
    summary: 'Angry summary',
    timestamp: '2024-01-01T12:00:00.000Z',
    color_key: 2,
  },
];

export const mockMusicList = ['track1.mp3', 'track2.mp3', 'track3.mp3'];

/**
 * Provider options for custom render
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Auth context initial values
  initialUser?: { id: string; name: string } | null;
  // Incident context initial values
  initialIncidentList?: any[];
  initialMusicList?: string[];
  // Whether to include providers
  withAuth?: boolean;
  withIncident?: boolean;
}

/**
 * Custom render function that wraps components with necessary providers
 */
export function renderWithProviders(
  ui: ReactElement,
  {
    initialUser = null,
    initialIncidentList = [],
    initialMusicList = [],
    withAuth = true,
    withIncident = true,
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  // Mock setters
  const mockSetUser = jest.fn();
  const mockSetIncidentList = jest.fn();
  const mockSetMusicList = jest.fn();

  // Create wrapper with specified providers
  function Wrapper({ children }: { children: React.ReactNode }) {
    let wrapped = <>{children}</>;

    if (withIncident) {
      // Mock IncidentProvider
      const IncidentContextValue = {
        incidentList: initialIncidentList,
        setIncidentList: mockSetIncidentList,
        musicList: initialMusicList,
        setMusicList: mockSetMusicList,
      };

      // We can't actually wrap with IncidentProvider here without implementing the full provider
      // So we'll just return the children and rely on component mocks
      wrapped = <IncidentProvider>{wrapped}</IncidentProvider>;
    }

    if (withAuth) {
      // Mock AuthProvider
      wrapped = <AuthProvider>{wrapped}</AuthProvider>;
    }

    return wrapped;
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    mockSetUser,
    mockSetIncidentList,
    mockSetMusicList,
  };
}

/**
 * Custom render with only AuthProvider
 */
export function renderWithAuth(ui: ReactElement, options: CustomRenderOptions = {}) {
  return renderWithProviders(ui, { ...options, withAuth: true, withIncident: false });
}

/**
 * Custom render with only IncidentProvider
 */
export function renderWithIncident(ui: ReactElement, options: CustomRenderOptions = {}) {
  return renderWithProviders(ui, { ...options, withAuth: false, withIncident: true });
}

/**
 * Mock AsyncStorage operations
 */
export const mockAsyncStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(),
  multiGet: jest.fn(),
  multiSet: jest.fn(),
  multiRemove: jest.fn(),
};

/**
 * Mock fetch with custom response
 */
export function mockFetch(response: any, ok: boolean = true, status: number = 200) {
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    status,
    json: jest.fn().mockResolvedValue(response),
    text: jest.fn().mockResolvedValue(JSON.stringify(response)),
  }) as jest.Mock;
}

/**
 * Mock fetch error
 */
export function mockFetchError(errorMessage: string, status: number = 500) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status,
    text: jest.fn().mockResolvedValue(errorMessage),
  }) as jest.Mock;
}

/**
 * Reset all mocks
 */
export function resetAllMocks() {
  jest.clearAllMocks();
  Object.values(mockAsyncStorage).forEach((mock) => mock.mockClear());
}

/**
 * Wait for async operations to complete
 */
export function waitFor(ms: number = 100) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Re-export everything from React Testing Library
export * from "@testing-library/react-native";
