/**
 * Global test setup and configuration
 * This file runs before all tests
 */

// Suppress console warnings/errors in tests unless explicitly testing them
global.console = {
  ...console,
  // Uncomment to suppress console output in tests
  // log: jest.fn(),
  // warn: jest.fn(),
  // error: jest.fn(),
};

// Set default timeout for async operations (increased for CI/slower machines)
jest.setTimeout(30000);

// Global setup for React Native components
if (typeof window !== 'undefined') {
  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
}

// Mock global fetch if not already mocked
if (!global.fetch) {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    })
  ) as jest.Mock;
}

// Reset mocks and AsyncStorage state before each test
beforeEach(() => {
  jest.clearAllMocks();
  const asyncStorage = require('@react-native-async-storage/async-storage');
  if (asyncStorage.__resetStore) asyncStorage.__resetStore();
});

// Clean up timers after each test to prevent Jest 30 teardown crashes.
// React Native's internal requestAnimationFrame can fire after environment
// teardown if timers are not cleared.
afterEach(() => {
  jest.clearAllTimers();
});
