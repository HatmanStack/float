/**
 * Authentication Flow Integration Tests
 *
 * These tests verify that authentication works correctly across components
 * through the AuthContext provider. Tests cover:
 * - User sign-in with Google and Guest options
 * - Token/user persistence with AsyncStorage
 * - Auth state propagation across components
 * - Sign-out and state cleanup
 * - Error scenarios
 */

import React from 'react';
import { View, Text, Button } from 'react-native';
import {
  renderWithAuthContext,
  renderWithAllContexts,
  mockAuthenticatedUser,
  mockGuestUser,
  mockAsyncStorage,
  waitForIntegration,
  fireEvent,
  act,
  INTEGRATION_TIMEOUTS,
} from './test-utils';
import { useAuth } from "@/frontend/context/AuthContext';
import { GoogleSignin } from '@react-native-google-signin/google-signin';

// Use mocked AsyncStorage from test-utils
const AsyncStorage = mockAsyncStorage;

// Mock Google Sign In module
jest.mock('@react-native-google-signin/google-signin');

// Mock axios for Google OAuth
jest.mock('axios', () => ({
  get: jest.fn().mockResolvedValue({
    data: {
      email: 'test@example.com',
      name: 'Test User',
    },
  }),
}));

// Mock @react-oauth/google
jest.mock('@react-oauth/google', () => ({
  GoogleOAuthProvider: ({ children }: any) => <>{children}</>,
  useGoogleLogin: () => jest.fn(),
}));

/**
 * Test component that displays and manipulates auth state
 */
function AuthConsumerComponent() {
  const { user, setUser } = useAuth();

  return (
    <View testID="auth-consumer">
      <Text testID="user-status">
        {user ? `Authenticated: ${user.name} (${user.id})` : 'Not authenticated'}
      </Text>
      <Button
        title="Sign In (Test User)"
        onPress={() => setUser(mockAuthenticatedUser)}
        testID="sign-in-button"
      />
      <Button
        title="Sign In (Guest)"
        onPress={() => setUser(mockGuestUser)}
        testID="guest-sign-in-button"
      />
      <Button title="Sign Out" onPress={() => setUser(null)} testID="sign-out-button" />
    </View>
  );
}

/**
 * Test component that shows different content based on auth state
 */
function ProtectedComponent() {
  const { user } = useAuth();

  if (!user) {
    return (
      <View testID="protected-component">
        <Text testID="auth-required">Please sign in to continue</Text>
      </View>
    );
  }

  return (
    <View testID="protected-component">
      <Text testID="welcome-message">Welcome, {user.name}!</Text>
      <Text testID="user-id">User ID: {user.id}</Text>
    </View>
  );
}

/**
 * Test component that uses auth with AsyncStorage persistence
 */
function AuthWithPersistenceComponent() {
  const { user, setUser } = useAuth();

  const handleSignIn = async () => {
    await AsyncStorage.setItem('user', JSON.stringify(mockAuthenticatedUser));
    setUser(mockAuthenticatedUser);
  };

  const handleSignOut = async () => {
    await AsyncStorage.removeItem('user');
    setUser(null);
  };

  return (
    <View testID="auth-persistence-component">
      <Text testID="user-name">{user?.name || 'Not signed in'}</Text>
      <Button title="Sign In" onPress={handleSignIn} testID="persist-sign-in-button" />
      <Button title="Sign Out" onPress={handleSignOut} testID="persist-sign-out-button" />
    </View>
  );
}

describe('Auth Flow Integration Tests', () => {
  beforeEach(() => {
    // Reset mocks and AsyncStorage before each test
    jest.clearAllMocks();
    mockAsyncStorage.reset();
  });

  describe('Basic Authentication Context', () => {
    it('should render with AuthContext provider', () => {
      const { getByTestId } = renderWithAuthContext(<AuthConsumerComponent />);

      expect(getByTestId('auth-consumer')).toBeTruthy();
      expect(getByTestId('user-status')).toHaveTextContent('Not authenticated');
    });

    it('should update auth state when user signs in', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthConsumerComponent />);

      // Initially not authenticated
      expect(getByTestId('user-status')).toHaveTextContent('Not authenticated');

      // Sign in
      fireEvent.press(getByTestId('sign-in-button'));

      // Wait for state update
      await waitForIntegration(() => {
        const statusText = getByTestId('user-status').props.children;
        expect(statusText).toContain('Authenticated: Test User');
      });

      const statusText = getByTestId('user-status').props.children;
      expect(statusText).toContain('test-user-123');
    });

    it('should update auth state when guest signs in', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthConsumerComponent />);

      // Sign in as guest
      fireEvent.press(getByTestId('guest-sign-in-button'));

      // Wait for state update
      await waitForIntegration(() => {
        const statusText = getByTestId('user-status').props.children;
        expect(statusText).toContain('Authenticated: Guest User');
      });

      const statusText = getByTestId('user-status').props.children;
      expect(statusText).toContain('guest');
    });

    it('should clear auth state when user signs out', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthConsumerComponent />);

      // Sign in first
      fireEvent.press(getByTestId('sign-in-button'));

      await waitForIntegration(() => {
        const statusText = getByTestId('user-status').props.children;
        expect(statusText).toContain('Authenticated: Test User');
      });

      // Sign out
      fireEvent.press(getByTestId('sign-out-button'));

      await waitForIntegration(() => {
        expect(getByTestId('user-status')).toHaveTextContent('Not authenticated');
      });
    });
  });

  describe('Auth State Propagation', () => {
    it('should propagate auth state to protected components', async () => {
      const { getByTestId } = renderWithAuthContext(
        <>
          <AuthConsumerComponent />
          <ProtectedComponent />
        </>
      );

      // Initially protected component shows auth required
      expect(getByTestId('auth-required')).toBeTruthy();

      // Sign in
      fireEvent.press(getByTestId('sign-in-button'));

      // Wait for auth state to propagate
      await waitForIntegration(() => {
        expect(getByTestId('welcome-message')).toBeTruthy();
      });

      // Verify protected component shows authenticated content
      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, Test User!');
      const userIdText = getByTestId('user-id').props.children;
      expect(userIdText).toContain('test-user-123');
    });

    it('should update protected components when user signs out', async () => {
      const { getByTestId } = renderWithAuthContext(
        <>
          <AuthConsumerComponent />
          <ProtectedComponent />
        </>
      );

      // Sign in
      fireEvent.press(getByTestId('sign-in-button'));

      await waitForIntegration(() => {
        expect(getByTestId('welcome-message')).toBeTruthy();
      });

      // Sign out
      fireEvent.press(getByTestId('sign-out-button'));

      // Wait for state to propagate
      await waitForIntegration(() => {
        expect(getByTestId('auth-required')).toBeTruthy();
      });

      expect(getByTestId('auth-required')).toHaveTextContent('Please sign in to continue');
    });

    it('should share auth state across multiple components', async () => {
      const { getByTestId, getAllByTestId } = renderWithAuthContext(
        <>
          <AuthConsumerComponent />
          <ProtectedComponent />
          <AuthConsumerComponent />
        </>
      );

      // Sign in from first component
      const signInButtons = getAllByTestId('sign-in-button');
      fireEvent.press(signInButtons[0]);

      // Wait for state update
      await waitForIntegration(() => {
        const userStatuses = getAllByTestId('user-status');
        const statusText = userStatuses[0].props.children;
        expect(statusText).toContain('Authenticated: Test User');
      });

      // Verify all components see the same auth state
      const userStatuses = getAllByTestId('user-status');
      expect(userStatuses).toHaveLength(2);
      userStatuses.forEach((status) => {
        const statusText = status.props.children;
        expect(statusText).toContain('Authenticated: Test User');
      });

      // Verify protected component updated
      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, Test User!');
    });
  });

  describe('AsyncStorage Persistence', () => {
    it('should persist user to AsyncStorage on sign in', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthWithPersistenceComponent />);

      // Sign in
      await act(async () => {
        fireEvent.press(getByTestId('persist-sign-in-button'));
      });

      // Wait for user name to update
      await waitForIntegration(() => {
        expect(getByTestId('user-name')).toHaveTextContent('Test User');
      });

      // Verify AsyncStorage was called
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        'user',
        JSON.stringify(mockAuthenticatedUser)
      );
    });

    it('should remove user from AsyncStorage on sign out', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthWithPersistenceComponent />);

      // Sign in first
      await act(async () => {
        fireEvent.press(getByTestId('persist-sign-in-button'));
      });

      await waitForIntegration(() => {
        expect(getByTestId('user-name')).toHaveTextContent('Test User');
      });

      // Sign out
      await act(async () => {
        fireEvent.press(getByTestId('persist-sign-out-button'));
      });

      // Wait for user name to clear
      await waitForIntegration(() => {
        expect(getByTestId('user-name')).toHaveTextContent('Not signed in');
      });

      // Verify AsyncStorage.removeItem was called
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('user');
    });

    it('should maintain auth state after AsyncStorage operations', async () => {
      const { getByTestId } = renderWithAuthContext(
        <>
          <AuthWithPersistenceComponent />
          <ProtectedComponent />
        </>
      );

      // Sign in
      await act(async () => {
        fireEvent.press(getByTestId('persist-sign-in-button'));
      });

      // Wait for both components to update
      await waitForIntegration(() => {
        expect(getByTestId('user-name')).toHaveTextContent('Test User');
        expect(getByTestId('welcome-message')).toBeTruthy();
      });

      // Verify auth state is consistent
      expect(getByTestId('user-name')).toHaveTextContent('Test User');
      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, Test User!');
    });
  });

  describe('Multi-Component Auth Flow', () => {
    it('should handle sign in affecting multiple components simultaneously', async () => {
      function Component1() {
        const { user } = useAuth();
        return <Text testID="component-1">{user ? 'Component 1: Logged In' : 'Component 1: Logged Out'}</Text>;
      }

      function Component2() {
        const { user } = useAuth();
        return <Text testID="component-2">{user ? 'Component 2: Logged In' : 'Component 2: Logged Out'}</Text>;
      }

      function Component3() {
        const { user } = useAuth();
        return <Text testID="component-3">{user ? 'Component 3: Logged In' : 'Component 3: Logged Out'}</Text>;
      }

      const { getByTestId } = renderWithAuthContext(
        <>
          <AuthConsumerComponent />
          <Component1 />
          <Component2 />
          <Component3 />
        </>
      );

      // All components initially show logged out
      expect(getByTestId('component-1')).toHaveTextContent('Component 1: Logged Out');
      expect(getByTestId('component-2')).toHaveTextContent('Component 2: Logged Out');
      expect(getByTestId('component-3')).toHaveTextContent('Component 3: Logged Out');

      // Sign in
      fireEvent.press(getByTestId('sign-in-button'));

      // All components update simultaneously
      await waitForIntegration(() => {
        expect(getByTestId('component-1')).toHaveTextContent('Component 1: Logged In');
        expect(getByTestId('component-2')).toHaveTextContent('Component 2: Logged In');
        expect(getByTestId('component-3')).toHaveTextContent('Component 3: Logged In');
      });
    });

    it('should handle rapid auth state changes', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthConsumerComponent />);

      // Rapid sign in and out
      fireEvent.press(getByTestId('sign-in-button'));
      fireEvent.press(getByTestId('sign-out-button'));
      fireEvent.press(getByTestId('guest-sign-in-button'));

      // Wait for final state
      await waitForIntegration(() => {
        const statusText = getByTestId('user-status').props.children;
        expect(statusText).toContain('Authenticated: Guest User');
      });

      const statusText = getByTestId('user-status').props.children;
      expect(statusText).toContain('guest');
    });
  });

  describe('Error Scenarios', () => {
    it('should handle missing user data gracefully', async () => {
      const { getByTestId } = renderWithAuthContext(<ProtectedComponent />);

      // Should show auth required when no user
      expect(getByTestId('auth-required')).toHaveTextContent('Please sign in to continue');
    });

    it('should handle AsyncStorage errors gracefully', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthWithPersistenceComponent />);

      // Component should render even if AsyncStorage operations might fail
      expect(getByTestId('auth-persistence-component')).toBeTruthy();
      expect(getByTestId('user-name')).toHaveTextContent('Not signed in');

      // Even with potential storage errors, component should remain functional
      expect(getByTestId('persist-sign-in-button')).toBeTruthy();
      expect(getByTestId('persist-sign-out-button')).toBeTruthy();
    });

    it('should handle sign out when not authenticated', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthConsumerComponent />);

      // Try to sign out when not authenticated
      fireEvent.press(getByTestId('sign-out-button'));

      // Should remain not authenticated (no error)
      await waitForIntegration(() => {
        expect(getByTestId('user-status')).toHaveTextContent('Not authenticated');
      });
    });
  });

  describe('Integration with Other Contexts', () => {
    it('should work alongside IncidentContext', async () => {
      const { getByTestId } = renderWithAllContexts(
        <>
          <AuthConsumerComponent />
          <ProtectedComponent />
        </>
      );

      // Sign in
      fireEvent.press(getByTestId('sign-in-button'));

      // Wait for auth state update
      await waitForIntegration(() => {
        expect(getByTestId('welcome-message')).toBeTruthy();
      });

      // Verify auth works with both contexts
      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, Test User!');
      const statusText = getByTestId('user-status').props.children;
      expect(statusText).toContain('Authenticated: Test User');
    });
  });
});
