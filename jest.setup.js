// Set environment variables for testing
process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL = 'https://mock-lambda-url.example.com';

// Set timezone to UTC for consistent date formatting in tests
process.env.TZ = 'UTC';

// Mock AsyncStorage globally for all tests
jest.mock('@react-native-async-storage/async-storage', () => {
  const store = new Map();
  return {
    getItem: jest.fn((key) => Promise.resolve(store.get(key) || null)),
    setItem: jest.fn((key, value) => {
      store.set(key, value);
      return Promise.resolve();
    }),
    removeItem: jest.fn((key) => {
      store.delete(key);
      return Promise.resolve();
    }),
    clear: jest.fn(() => {
      store.clear();
      return Promise.resolve();
    }),
    getAllKeys: jest.fn(() => Promise.resolve(Array.from(store.keys()))),
    multiGet: jest.fn((keys) =>
      Promise.resolve(keys.map((key) => [key, store.get(key) || null]))
    ),
    multiSet: jest.fn((pairs) => {
      pairs.forEach(([key, value]) => store.set(key, value));
      return Promise.resolve();
    }),
    multiRemove: jest.fn((keys) => {
      keys.forEach((key) => store.delete(key));
      return Promise.resolve();
    }),
  };
});
