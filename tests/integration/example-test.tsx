/**
 * Example Integration Test
 *
 * This test demonstrates how to write integration tests
 * and verifies that the integration test infrastructure works correctly.
 */

import React from 'react';
import { View, Text, Button } from 'react-native';
import {
  renderWithAuthContext,
  renderWithIncidentContext,
  renderWithAllContexts,
  mockAuthenticatedUser,
  mockIncidentList,
  waitForIntegration,
  fireEvent,
  within,
} from './test-utils';
import { useAuth } from '@/frontend/context/AuthContext';
import { useIncident } from '@/frontend/context/IncidentContext';

/**
 * Test component that uses AuthContext
 */
function AuthTestComponent() {
  const { user, setUser } = useAuth();

  return (
    <View testID="auth-test-component">
      <Text testID="user-status">{user ? `Logged in as ${user.name}` : 'Not logged in'}</Text>
      <Button
        title="Sign In"
        onPress={() => setUser(mockAuthenticatedUser)}
        testID="sign-in-button"
      />
      <Button title="Sign Out" onPress={() => setUser(null)} testID="sign-out-button" />
    </View>
  );
}

/**
 * Test component that uses IncidentContext
 */
function IncidentTestComponent() {
  const { incidentList, setIncidentList } = useIncident();

  return (
    <View testID="incident-test-component">
      <Text testID="incident-count">Incidents: {incidentList.length}</Text>
      <Button
        title="Add Incident"
        onPress={() =>
          setIncidentList([
            ...incidentList,
            {
              id: `incident-${Date.now()}`,
              timestamp: new Date(),
              sentiment_label: 'Test',
              intensity: 3,
              summary: 'Test incident',
            },
          ])
        }
        testID="add-incident-button"
      />
      <Button title="Clear Incidents" onPress={() => setIncidentList([])} testID="clear-button" />
    </View>
  );
}

/**
 * Test component that uses both contexts
 */
function MultiContextTestComponent() {
  const { user } = useAuth();
  const { incidentList } = useIncident();

  return (
    <View testID="multi-context-component">
      <Text testID="user-name">{user?.name || 'Guest'}</Text>
      <Text testID="incident-count">{incidentList.length} incidents</Text>
    </View>
  );
}

describe('Integration Test Infrastructure', () => {
  describe('AuthContext Integration', () => {
    it('should render with AuthContext provider', () => {
      const { getByTestId } = renderWithAuthContext(<AuthTestComponent />);

      expect(getByTestId('auth-test-component')).toBeTruthy();
      expect(getByTestId('user-status')).toHaveTextContent('Not logged in');
    });

    it('should update auth state when user signs in', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthTestComponent />);

      // Initially not logged in
      expect(getByTestId('user-status')).toHaveTextContent('Not logged in');

      // Sign in
      const signInButton = getByTestId('sign-in-button');
      fireEvent.press(signInButton);

      // Wait for state update
      await waitForIntegration(() => {
        expect(getByTestId('user-status')).toHaveTextContent('Logged in as Test User');
      });
    });

    it('should update auth state when user signs out', async () => {
      const { getByTestId } = renderWithAuthContext(<AuthTestComponent />);

      // Sign in first
      fireEvent.press(getByTestId('sign-in-button'));

      await waitForIntegration(() => {
        expect(getByTestId('user-status')).toHaveTextContent('Logged in as Test User');
      });

      // Sign out
      fireEvent.press(getByTestId('sign-out-button'));

      await waitForIntegration(() => {
        expect(getByTestId('user-status')).toHaveTextContent('Not logged in');
      });
    });
  });

  describe('IncidentContext Integration', () => {
    it('should render with IncidentContext provider', () => {
      const { getByTestId } = renderWithIncidentContext(<IncidentTestComponent />);

      expect(getByTestId('incident-test-component')).toBeTruthy();
      expect(getByTestId('incident-count')).toHaveTextContent('Incidents: 0');
    });

    it('should add incident when button pressed', async () => {
      const { getByTestId } = renderWithIncidentContext(<IncidentTestComponent />);

      // Initially no incidents
      expect(getByTestId('incident-count')).toHaveTextContent('Incidents: 0');

      // Add incident
      fireEvent.press(getByTestId('add-incident-button'));

      // Wait for state update
      await waitForIntegration(() => {
        expect(getByTestId('incident-count')).toHaveTextContent('Incidents: 1');
      });
    });

    it('should clear incidents when clear button pressed', async () => {
      const { getByTestId } = renderWithIncidentContext(<IncidentTestComponent />);

      // Add some incidents
      fireEvent.press(getByTestId('add-incident-button'));
      fireEvent.press(getByTestId('add-incident-button'));

      await waitForIntegration(() => {
        expect(getByTestId('incident-count')).toHaveTextContent('Incidents: 2');
      });

      // Clear incidents
      fireEvent.press(getByTestId('clear-button'));

      await waitForIntegration(() => {
        expect(getByTestId('incident-count')).toHaveTextContent('Incidents: 0');
      });
    });
  });

  describe('Multiple Contexts Integration', () => {
    it('should render with both context providers', () => {
      const { getByTestId } = renderWithAllContexts(<MultiContextTestComponent />);

      expect(getByTestId('multi-context-component')).toBeTruthy();
      expect(getByTestId('user-name')).toHaveTextContent('Guest');
      expect(getByTestId('incident-count')).toHaveTextContent('0 incidents');
    });

    it('should update both contexts independently', async () => {
      const { getByTestId } = renderWithAllContexts(
        <>
          <AuthTestComponent />
          <IncidentTestComponent />
          <MultiContextTestComponent />
        </>
      );

      // Sign in
      fireEvent.press(getByTestId('sign-in-button'));

      await waitForIntegration(() => {
        expect(getByTestId('user-name')).toHaveTextContent('Test User');
      });

      // Add incident
      fireEvent.press(getByTestId('add-incident-button'));

      // Check the incident count in the multi-context component specifically
      await waitForIntegration(() => {
        const multiContextComponent = getByTestId('multi-context-component');
        expect(within(multiContextComponent).getByTestId('incident-count')).toHaveTextContent(
          '1 incidents'
        );
      });

      // Verify both states persisted in the multi-context component
      const multiContextComponent = getByTestId('multi-context-component');
      expect(within(multiContextComponent).getByTestId('user-name')).toHaveTextContent('Test User');
      expect(within(multiContextComponent).getByTestId('incident-count')).toHaveTextContent(
        '1 incidents'
      );
    });
  });
});
