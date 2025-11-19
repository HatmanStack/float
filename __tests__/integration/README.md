# Integration Tests

This directory contains integration tests for the Float meditation app.

## What are Integration Tests?

Integration tests verify that multiple components work together correctly through shared state and Context providers. They sit between unit tests (single component) and E2E tests (full application).

**Differences from Component Tests:**
- **Component Tests**: Test a single component in isolation with mocked dependencies
- **Integration Tests**: Test multiple components interacting through real Context providers
- **E2E Tests**: Test complete user flows through the entire application

## Test Organization

```
__tests__/integration/
├── setup.ts                    # Test environment configuration
├── test-utils.tsx              # Integration test utilities
├── auth-flow-test.tsx          # Authentication flow integration tests
├── recording-flow-test.tsx     # Recording flow integration tests
└── meditation-flow-test.tsx    # Meditation flow integration tests
```

## Writing Integration Tests

### Basic Example

```typescript
import { renderIntegration, mockAuthenticatedUser, waitForIntegration } from './test-utils';
import { MyComponent } from '@/components/MyComponent';

describe('MyComponent Integration', () => {
  it('should update Context when user interacts', async () => {
    const { getByText, getByTestId } = renderIntegration(<MyComponent />);

    // Interact with component
    const button = getByText('Submit');
    fireEvent.press(button);

    // Wait for Context update
    await waitForIntegration(() => {
      expect(getByTestId('status')).toHaveTextContent('Submitted');
    });
  });
});
```

### Testing with Context

```typescript
import { renderWithAuthContext } from './test-utils';
import { useAuth } from '@/context/AuthContext';

function TestComponent() {
  const { user, setUser } = useAuth();

  return (
    <View>
      <Text testID="user-name">{user?.name || 'Not logged in'}</Text>
      <Button
        title="Sign In"
        onPress={() => setUser(mockAuthenticatedUser)}
      />
    </View>
  );
}

describe('Auth Context Integration', () => {
  it('should share auth state across components', async () => {
    const { getByText, getByTestId } = renderWithAuthContext(<TestComponent />);

    // Initially not logged in
    expect(getByTestId('user-name')).toHaveTextContent('Not logged in');

    // Sign in
    fireEvent.press(getByText('Sign In'));

    // Wait for Context update
    await waitForIntegration(() => {
      expect(getByTestId('user-name')).toHaveTextContent('Test User');
    });
  });
});
```

### Testing Multi-Component Flows

```typescript
import { renderWithAllContexts, mockIncident } from './test-utils';

describe('Recording to Summary Flow', () => {
  it('should update incident list when summary completes', async () => {
    const { getByText } = renderWithAllContexts(
      <>
        <AudioRecording />
        <History />
      </>
    );

    // Start recording
    fireEvent.press(getByText('Record'));

    // Stop recording
    await waitForIntegration(() => getByText('Stop'));
    fireEvent.press(getByText('Stop'));

    // Wait for summary to complete and update Context
    await waitForIntegration(() => {
      expect(getByText('Happy')).toBeTruthy();
    }, { timeout: 5000 });
  });
});
```

## Available Utilities

### Render Functions

- `renderIntegration(ui, options)` - Render with both Context providers
- `renderWithAuthContext(ui, options)` - Render with only AuthProvider
- `renderWithIncidentContext(ui, options)` - Render with only IncidentProvider
- `renderWithAllContexts(ui, options)` - Explicit render with all providers

### Mocks

- `mockAuthenticatedUser` - Mock authenticated user data
- `mockGuestUser` - Mock guest user data
- `mockIncident` - Single mock incident
- `mockIncidentList` - Array of mock incidents
- `mockMusicList` - Array of mock meditation tracks
- `mockAsyncStorage` - Mock AsyncStorage with in-memory store
- `mockNavigation` - Mock navigation object
- `mockFetchSuccess(response, status)` - Mock successful API call
- `mockFetchError(message, status)` - Mock failed API call
- `mockNetworkError(message)` - Mock network error

### Utilities

- `waitForIntegration(callback, options)` - Wait for async operations with longer timeout
- `resetAllMocks()` - Reset all mocks between tests
- `INTEGRATION_TIMEOUTS` - Recommended timeout constants

## Running Integration Tests

```bash
# Run all integration tests
npm test -- __tests__/integration/ --watchAll=false

# Run specific integration test file
npm test -- __tests__/integration/auth-flow-test.tsx

# Run with verbose output
npm test -- __tests__/integration/ --verbose

# Run with coverage
npm test -- __tests__/integration/ --coverage --watchAll=false
```

## Best Practices

1. **Use Real Context Providers**
   - Integration tests use real Context, not mocks
   - This tests actual state management logic

2. **Test Component Interactions**
   - Test how components communicate through Context
   - Verify state changes propagate correctly

3. **Mock External Dependencies**
   - Mock backend API calls
   - Mock platform-specific APIs (Audio, FileSystem)
   - Don't mock Context providers

4. **Use Appropriate Timeouts**
   - Integration tests are slower than unit tests
   - Use `waitForIntegration` with appropriate timeouts
   - Default timeout is 3000ms (vs 1000ms for unit tests)

5. **Test Realistic Scenarios**
   - Test common user workflows
   - Test error scenarios
   - Test state consistency across components

6. **Maintain Test Isolation**
   - Reset mocks between tests
   - Clear Context state between tests
   - Use `afterEach(() => resetAllMocks())`

## Common Patterns

### Testing Context State Changes

```typescript
it('should update Context when user signs in', async () => {
  const { getByTestId } = renderWithAuthContext(<AuthScreen />);

  fireEvent.press(getByTestId('sign-in-button'));

  await waitForIntegration(() => {
    expect(getByTestId('user-name')).toHaveTextContent('Test User');
  });
});
```

### Testing API Integration

```typescript
it('should handle API errors gracefully', async () => {
  mockFetchError('Server error', 500);

  const { getByText } = renderIntegration(<SummaryComponent />);

  fireEvent.press(getByText('Generate Summary'));

  await waitForIntegration(() => {
    expect(getByText(/error/i)).toBeTruthy();
  });
});
```

### Testing Multi-Component State Sharing

```typescript
it('should share incident state across components', async () => {
  const { getByTestId } = renderWithIncidentContext(
    <>
      <IncidentCreator />
      <IncidentList />
    </>
  );

  // Create incident in one component
  fireEvent.press(getByTestId('create-incident'));

  // Verify it appears in another component
  await waitForIntegration(() => {
    expect(getByTestId('incident-list')).toContainElement(
      getByTestId('incident-item-0')
    );
  });
});
```

## Troubleshooting

### Test Timeout

If tests timeout, increase the timeout:

```typescript
await waitForIntegration(
  () => expect(element).toBeTruthy(),
  { timeout: 5000 }
);
```

### Context Not Updating

Make sure you're using real providers:

```typescript
// ✅ Good - uses real provider
renderIntegration(<Component />);

// ❌ Bad - uses mocked provider
render(<Component />);
```

### Async State Issues

Use `waitForIntegration` for all async operations:

```typescript
// ✅ Good
await waitForIntegration(() => {
  expect(element).toHaveTextContent('Updated');
});

// ❌ Bad - may not wait for state update
expect(element).toHaveTextContent('Updated');
```
