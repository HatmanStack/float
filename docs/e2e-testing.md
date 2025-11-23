# End-to-End Testing with Detox

This directory contains E2E tests for the Float meditation app using Detox.

## Overview

E2E tests verify complete user journeys through the application, testing the integration of all components, navigation, and backend interactions.

**Test Coverage:**

- Complete user journey (auth → record → summary → meditation → playback)
- Error scenarios and recovery flows
- Navigation and screen transitions
- Backend API integration
- Permission handling

## Prerequisites

### iOS Testing

- macOS with Xcode installed
- iOS Simulator configured
- Node.js 24.x
- Detox CLI: `npm install -g detox-cli`

### Android Testing

- Android Studio installed
- Android SDK configured
- Android Emulator (AVD) created: `Pixel_5_API_31`
- Node.js 24.x
- Detox CLI: `npm install -g detox-cli`

## Setup

### 1. Install Dependencies

```bash
npm install --save-dev detox jest
```

### 2. Build the App

**iOS:**

```bash
detox build --configuration ios.sim.debug
```

**Android:**

```bash
detox build --configuration android.emu.debug
```

### 3. Create Android AVD (if needed)

```bash
# List available system images
sdkmanager --list | grep system-images

# Download Android 31 system image
sdkmanager "system-images;android-31;google_apis;x86_64"

# Create AVD
avdmanager create avd -n Pixel_5_API_31 -k "system-images;android-31;google_apis;x86_64" -d "pixel_5"
```

## Running Tests

### Run All E2E Tests

**iOS:**

```bash
detox test --configuration ios.sim.debug
```

**Android:**

```bash
detox test --configuration android.emu.debug
```

### Run Specific Test

```bash
detox test --configuration android.emu.debug e2e/complete-user-journey.e2e.ts
```

### Run with Verbose Output

```bash
detox test --configuration ios.sim.debug --loglevel verbose
```

### Run and Take Screenshots

```bash
detox test --configuration android.emu.debug --take-screenshots all
```

## Test Structure

```
e2e/
├── jest.config.js              # Jest configuration for Detox
├── init.ts                     # E2E test initialization (planned)
├── helpers/                    # Test helper functions (planned)
│   ├── navigation.ts           # Navigation helpers
│   ├── authentication.ts       # Auth helpers
│   └── backend-mocks.ts        # Backend mocking
├── complete-user-journey.e2e.ts    # Main user flow (planned)
└── error-scenarios.e2e.ts          # Error handling (planned)
```

## Writing E2E Tests

### Basic Test Structure

```typescript
import { by, device, element, expect } from 'detox';

describe('Feature Name', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should complete user action', async () => {
    // Wait for element
    await waitFor(element(by.id('button-id')))
      .toBeVisible()
      .withTimeout(5000);

    // Tap element
    await element(by.id('button-id')).tap();

    // Verify result
    await expect(element(by.id('result-id'))).toHaveText('Expected Text');
  });
});
```

### Matchers

Detox provides various matchers:

```typescript
// Visibility
await expect(element(by.id('element'))).toBeVisible();
await expect(element(by.id('element'))).toBeNotVisible();

// Text content
await expect(element(by.id('element'))).toHaveText('text');
await expect(element(by.id('element'))).toHaveLabel('label');

// Existence
await expect(element(by.id('element'))).toExist();
await expect(element(by.id('element'))).not.toExist();
```

### Actions

```typescript
// Tap
await element(by.id('button')).tap();

// Type text
await element(by.id('input')).typeText('Hello');

// Scroll
await element(by.id('scrollview')).scrollTo('bottom');

// Swipe
await element(by.id('element')).swipe('up');

// Wait for element
await waitFor(element(by.id('element')))
  .toBeVisible()
  .withTimeout(5000);
```

### Selectors

```typescript
// By ID (testID prop)
element(by.id('my-element-id'));

// By text
element(by.text('Sign In'));

// By label
element(by.label('Username'));

// By type
element(by.type('RCTTextInput'));

// Combined matchers
element(by.id('button').and(by.text('Submit')));
```

## Best Practices

1. **Use testID Props**
   - Always add testID to elements you'll interact with in E2E tests
   - Use descriptive, unique testIDs

2. **Wait for Elements**
   - Always use `waitFor()` for async operations
   - Set appropriate timeouts (network calls may take time)

3. **Mock Backend Responses**
   - Use deterministic test data
   - Mock API calls for faster, more reliable tests

4. **Keep Tests Focused**
   - Each test should verify one user flow
   - Avoid overly long test scenarios

5. **Clean Up Between Tests**
   - Use `beforeEach` to reset app state
   - Clear any persisted data

6. **Handle Permissions**
   - Grant permissions programmatically in tests
   - Don't rely on permission prompts

## Current E2E Test Plan

### Complete User Journey (Planned)

- Launch app
- Sign in (mock authentication)
- Navigate to recording screen
- Grant microphone permission
- Record audio (3 seconds)
- Stop recording
- Wait for summary generation
- Verify summary displayed (sentiment, intensity)
- Generate meditation from summary
- Play meditation
- Navigate to history
- Verify incident in history

### Error Scenarios (Planned)

- Offline mode (network error)
- Permission denial
- Backend errors (500, 400)
- Invalid audio input
- Timeout scenarios

## CI/CD Integration

### GitHub Actions (Example)

```yaml
name: E2E Tests

on: [pull_request]

jobs:
  e2e-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '24'
      - run: npm install
      - run: detox build --configuration android.emu.debug
      - uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 31
          target: google_apis
          arch: x86_64
          script: detox test --configuration android.emu.debug
```

## Troubleshooting

### App Won't Build

```bash
# Clean build artifacts
rm -rf android/build
rm -rf android/app/build
cd android && ./gradlew clean
```

### Tests Timeout

- Increase timeout in jest.config.js
- Check emulator/simulator performance
- Verify backend mocks are working

### Element Not Found

- Verify testID is set correctly
- Use `detox test --loglevel trace` for detailed logs
- Check element visibility (may be off-screen)

### Emulator Issues

```bash
# List running emulators
adb devices

# Restart emulator
adb reboot

# Cold boot emulator
emulator -avd Pixel_5_API_31 -no-snapshot-load
```

## Status

**Current Implementation:**

- ✅ Detox configuration created (.detoxrc.js)
- ✅ Jest E2E configuration created
- ✅ Documentation complete
- ⏳ E2E test files (planned, not executed - requires emulator/simulator)
- ⏳ Helper utilities (planned)

**Note:** Actual E2E test execution requires:

- Native app builds (iOS/Android)
- Emulator/simulator setup
- Can be run locally or in CI/CD

Integration tests in `__tests__/integration/` provide comprehensive coverage of component interactions without requiring native builds.
