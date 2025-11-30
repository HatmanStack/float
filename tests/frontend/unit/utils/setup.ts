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

// Global test constants
export const TEST_TIMEOUT = 5000;
export const ASYNC_WAIT_TIME = 100;

// Common mock data
export const MOCK_API_URL = 'https://mock-api.example.com';
export const MOCK_LAMBDA_URL = 'https://mock-lambda.example.com';

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

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});
