// Polyfill expo 55 globals for jest
// Must run before test framework loads modules

if (!globalThis.__ExpoImportMetaRegistry) {
  globalThis.__ExpoImportMetaRegistry = {
    register: () => {},
    get: () => ({}),
  };
}

if (typeof globalThis.structuredClone === 'undefined') {
  globalThis.structuredClone = (val) => JSON.parse(JSON.stringify(val));
}

// Clean up timers after each test to prevent Jest 30 teardown crashes.
// React Native's internal requestAnimationFrame can fire after environment
// teardown if timers are not cleared.
afterEach(() => {
  jest.clearAllTimers();
});
