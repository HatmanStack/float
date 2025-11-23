# Testing Guide

This document provides comprehensive information about testing in the Float application.

## Table of Contents

- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [Writing Tests](#writing-tests)
- [Mock Patterns](#mock-patterns)
- [Test Utilities](#test-utilities)
- [Coverage](#coverage)
- [Best Practices](#best-practices)

## Running Tests

### Run All Tests

```bash
npm test
```

### Run Tests in Watch Mode

```bash
npm test -- --watch
```

### Run Specific Test File

```bash
npm test -- ComponentName-test.tsx
```

### Run Tests with Coverage

```bash
npm test -- --coverage
```

### Run Tests Without Watch Mode

```bash
npm test -- --watchAll=false
```

## Test Organization

### Directory Structure

```
components/
├── __tests__/
│   ├── utils/
│   │   ├── setup.ts          # Global test configuration
│   │   └── testUtils.tsx     # Shared test utilities
│   ├── Component1-test.tsx
│   ├── Component2-test.tsx
│   └── ...
├── Component1.tsx
├── Component2.tsx
└── ...
```

### Naming Conventions

- Test files: `ComponentName-test.tsx`
- Test suites: `describe('ComponentName', () => { ... })`
- Test cases: `it('should do something specific', () => { ... })`

### Test File Structure

```typescript
// 1. Mock dependencies BEFORE imports
jest.mock('@/context/SomeContext', () => ({
  useSomeContext: () => ({
    someValue: 'mock-value',
  }),
}));

// 2. Import component under test
import { MyComponent } from '@/components/MyComponent';

// 3. Describe test suite
describe('MyComponent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing', () => {
    const { toJSON } = render(<MyComponent />);
    expect(toJSON()).toBeTruthy();
  });

  // More tests...
});
```

## Writing Tests

### Basic Component Test

```typescript
import { render } from '@testing-library/react-native';
import { MyComponent } from '@/components/MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    const { getByText } = render(<MyComponent />);
    expect(getByText('Expected Text')).toBeTruthy();
  });
});
```

### Testing User Interactions

```typescript
import { render, fireEvent } from '@testing-library/react-native';

it('should handle button press', () => {
  const mockOnPress = jest.fn();
  const { getByText } = render(<MyButton onPress={mockOnPress} />);

  fireEvent.press(getByText('Click Me'));

  expect(mockOnPress).toHaveBeenCalledTimes(1);
});
```

### Testing Async Operations

```typescript
import { render, waitFor } from '@testing-library/react-native';

it('should load data asynchronously', async () => {
  const { getByText } = render(<MyComponent />);

  await waitFor(() => {
    expect(getByText('Loaded Data')).toBeTruthy();
  });
});
```

### Testing with Context

```typescript
import { renderWithProviders } from '../utils/testUtils';

it('should access context data', () => {
  const { getByText } = renderWithProviders(<MyComponent />, {
    initialUser: { id: '123', name: 'Test User' },
  });

  expect(getByText('Test User')).toBeTruthy();
});
```

## Mock Patterns

### Mocking React Native Components

```typescript
jest.mock('@/components/ThemedView', () => ({
  ThemedView: ({ children, style, ...props }: any) => {
    const { View } = require('react-native');
    return <View style={style} {...props}>{children}</View>;
  },
}));
```

### Mocking Context

```typescript
const mockSetUser = jest.fn();

jest.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    setUser: mockSetUser,
  }),
}));
```

### Mocking AsyncStorage

```typescript
jest.mock('@react-native-async-storage/async-storage', () => ({
  __esModule: true,
  default: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
}));

import AsyncStorage from '@react-native-async-storage/async-storage';

beforeEach(() => {
  (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);
  (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
});
```

### Mocking fetch

```typescript
beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: jest.fn().mockResolvedValue({ data: 'mock-data' }),
  }) as jest.Mock;
});

afterEach(() => {
  jest.clearAllMocks();
});
```

### Mocking Expo Modules

```typescript
// expo-notifications
jest.mock('expo-notifications', () => ({
  addNotificationReceivedListener: jest.fn(),
  removeNotificationSubscription: jest.fn(),
  getExpoPushTokenAsync: jest.fn().mockResolvedValue({ data: 'mock-token' }),
}));

// expo-file-system
jest.mock('expo-file-system', () => ({
  documentDirectory: 'mock-directory/',
  writeAsStringAsync: jest.fn(),
  readAsStringAsync: jest.fn(),
  deleteAsync: jest.fn(),
  EncodingType: {
    Base64: 'base64',
  },
}));
```

### Mocking Platform

```typescript
import { Platform } from 'react-native';

beforeEach(() => {
  // @ts-ignore
  Platform.OS = 'ios'; // or 'android', 'web'
});
```

## Test Utilities

### Custom Render Functions

Located in `components/__tests__/utils/testUtils.tsx`:

#### renderWithProviders

Renders component with Auth and Incident context providers:

```typescript
import { renderWithProviders } from '../utils/testUtils';

const { getByText, mockSetUser } = renderWithProviders(<MyComponent />, {
  initialUser: { id: '123', name: 'Test User' },
  initialIncidentList: [{ /* incident data */ }],
});
```

#### Mock Data Factories

```typescript
import {
  mockUser,
  mockGuestUser,
  mockIncident,
  mockIncidentList,
  mockMusicList,
} from '../utils/testUtils';

// Use in tests
const user = mockUser; // { id: 'test-user-123', name: 'Test User' }
```

#### Helper Functions

```typescript
import { mockFetch, mockFetchError, resetAllMocks, waitFor } from '../utils/testUtils';

// Mock successful fetch
mockFetch({ data: 'response' });

// Mock fetch error
mockFetchError('Server Error', 500);

// Reset all mocks
resetAllMocks();

// Wait for async operations
await waitFor(100);
```

## Coverage

### Current Coverage

As of the latest update:

- **Test Suites:** 15 passing
- **Tests:** 103 passing
- **Component Coverage:** ~82%

### Coverage by Component

| Component             | Tests    | Coverage |
| --------------------- | -------- | -------- |
| BackendSummaryCall    | 6        | 75%+     |
| BackendMeditationCall | 7        | 72%+     |
| AudioRecording        | 13       | 85%+     |
| LocalFileLoadAndSave  | 4        | 60%+     |
| ThemedView            | 8        | 85%+     |
| ParallaxScrollView    | 9        | 71%+     |
| Collapsible           | 10       | 76%+     |
| Notifications         | 10       | 77%+     |
| History               | 10       | 76%+     |
| AuthScreen            | 10       | 78%+     |
| IncidentItem          | Existing | 80%+     |
| IncidentColoring      | Existing | 90%+     |
| MeditationControls    | Existing | 75%+     |
| Guidance              | Existing | 75%+     |
| ThemedText            | Existing | 85%+     |

### Viewing Coverage Reports

```bash
npm test -- --coverage --coverageDirectory=coverage
```

Open `coverage/lcov-report/index.html` in a browser to view detailed coverage.

## Best Practices

### 1. Test Behavior, Not Implementation

**Good:**

```typescript
it('should display user name when logged in', () => {
  const { getByText } = render(<Profile user={{ name: 'John' }} />);
  expect(getByText('John')).toBeTruthy();
});
```

**Bad:**

```typescript
it('should call setState with user name', () => {
  // Testing implementation details
});
```

### 2. Use Descriptive Test Names

**Good:**

```typescript
it('should show error message when login fails', () => { ... });
it('should disable submit button while loading', () => { ... });
```

**Bad:**

```typescript
it('test 1', () => { ... });
it('works', () => { ... });
```

### 3. Arrange, Act, Assert (AAA)

```typescript
it('should update user profile', async () => {
  // Arrange
  const mockUser = { id: '123', name: 'John' };
  const { getByText } = render(<Profile user={mockUser} />);

  // Act
  fireEvent.press(getByText('Update Profile'));

  // Assert
  await waitFor(() => {
    expect(getByText('Profile Updated')).toBeTruthy();
  });
});
```

### 4. Mock External Dependencies

Always mock:

- API calls (fetch, axios)
- Native modules (expo-\*, react-native modules)
- Third-party libraries
- Context providers (when testing components in isolation)

### 5. Test Edge Cases

```typescript
describe('Input validation', () => {
  it('should handle empty input', () => { ... });
  it('should handle very long input', () => { ... });
  it('should handle special characters', () => { ... });
  it('should handle null/undefined', () => { ... });
});
```

### 6. Keep Tests Independent

Each test should be able to run in isolation:

```typescript
beforeEach(() => {
  jest.clearAllMocks();
  // Reset any global state
});

afterEach(() => {
  // Clean up
});
```

### 7. Avoid Test Interdependencies

**Good:**

```typescript
it('should add item', () => {
  const { getByText } = render(<List />);
  fireEvent.press(getByText('Add'));
  expect(getByText('New Item')).toBeTruthy();
});

it('should remove item', () => {
  const { getByText } = render(<List items={[{ id: 1 }]} />);
  fireEvent.press(getByText('Remove'));
  expect(queryByText('Item 1')).toBeNull();
});
```

**Bad:**

```typescript
// Don't rely on previous test state
let sharedState;

it('should add item', () => {
  sharedState = addItem();
});

it('should remove item', () => {
  removeItem(sharedState); // Depends on previous test
});
```

### 8. Use waitFor for Async Operations

```typescript
it('should load data', async () => {
  const { getByText } = render(<DataLoader />);

  await waitFor(() => {
    expect(getByText('Data Loaded')).toBeTruthy();
  }, { timeout: 3000 });
});
```

### 9. Test Accessibility

```typescript
it('should be accessible', () => {
  const { getByLabelText } = render(<LoginForm />);
  expect(getByLabelText('Email')).toBeTruthy();
  expect(getByLabelText('Password')).toBeTruthy();
});
```

### 10. Clean Up After Tests

```typescript
afterEach(() => {
  jest.clearAllMocks();
  // Clear any timers
  jest.clearAllTimers();
  // Restore any spies
  jest.restoreAllMocks();
});
```

## Common Issues and Solutions

### Issue: Tests timeout

**Solution:** Increase timeout or ensure async operations complete:

```typescript
it('long running test', async () => {
  // ... test code
}, 10000); // 10 second timeout
```

### Issue: Mock not working

**Solution:** Ensure mocks are defined BEFORE imports:

```typescript
// ✓ Correct
jest.mock('./myModule');
import { myFunction } from './myModule';

// ✗ Wrong
import { myFunction } from './myModule';
jest.mock('./myModule');
```

### Issue: State updates not reflected

**Solution:** Use waitFor or act:

```typescript
import { waitFor } from '@testing-library/react-native';

await waitFor(() => {
  expect(getByText('Updated')).toBeTruthy();
});
```

### Issue: Cannot find element

**Solution:** Check component actually renders the element:

```typescript
// Debug what's rendered
const { debug } = render(<MyComponent />);
debug(); // Prints component tree
```

## Additional Resources

- [Jest Documentation](https://jestjs.io/)
- [React Native Testing Library](https://callstack.github.io/react-native-testing-library/)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Jest Expo Preset](https://docs.expo.dev/guides/testing-with-jest/)

## Contributing

When adding new tests:

1. Follow the naming conventions
2. Use shared test utilities when possible
3. Mock external dependencies
4. Write descriptive test names
5. Ensure tests pass locally before committing
6. Update this documentation if adding new patterns

## Questions?

For questions about testing:

1. Check this documentation
2. Review existing test files for examples
3. Consult the team

---

Last updated: Phase 4 completion (November 2024)
