/**
 * Complete User Journey E2E Tests
 *
 * These tests verify the entire user flow from authentication
 * through recording, summary generation, meditation, and history.
 *
 * @requires Detox configured and app built
 * @requires Backend API mocked or available
 */

import { by, device, element, expect as detoxExpect, waitFor } from "detox";

describe('Complete User Journey', () => {
  beforeAll(async () => {
    await device.launchApp({
      newInstance: true,
      permissions: { notifications: 'YES', microphone: 'YES' },
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  describe('Guest User Complete Flow', () => {
    it('should complete full journey: auth → record → summary → meditation → history', async () => {
      // Step 1: Authentication
      await waitFor(element(by.text('Guest User')))
        .toBeVisible()
        .withTimeout(5000);

      await element(by.text('Guest User')).tap();

      // Verify authenticated
      await waitFor(element(by.text('Welcome back!')))
        .toBeVisible()
        .withTimeout(3000);

      // Step 2: Navigate to recording screen
      await element(by.id('tab-recording')).tap();

      // Step 3: Start recording
      await waitFor(element(by.id('record-button')))
        .toBeVisible()
        .withTimeout(3000);

      await element(by.id('record-button')).tap();

      // Verify recording started
      await waitFor(element(by.id('recording-status')))
        .toHaveText('Recording...')
        .withTimeout(2000);

      // Step 4: Record for 3 seconds
      await new Promise((resolve) => setTimeout(resolve, 3000));

      // Step 5: Stop recording
      await element(by.id('stop-button')).tap();

      // Verify recording stopped
      await waitFor(element(by.id('recording-status')))
        .toHaveText('Processing...')
        .withTimeout(2000);

      // Step 6: Wait for summary generation
      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000); // Backend call may take time

      // Verify summary content
      await detoxExpect(element(by.id('sentiment-label'))).toBeVisible();
      await detoxExpect(element(by.id('intensity-value'))).toBeVisible();

      // Step 7: Generate meditation from summary
      await element(by.id('generate-meditation-button')).tap();

      // Wait for meditation generation
      await waitFor(element(by.id('meditation-ready')))
        .toBeVisible()
        .withTimeout(30000);

      // Step 8: Play meditation
      await element(by.id('play-meditation-button')).tap();

      // Verify playback started
      await waitFor(element(by.id('playback-status')))
        .toHaveText('Playing')
        .withTimeout(2000);

      // Step 9: Navigate to history
      await element(by.id('tab-history')).tap();

      // Verify incident appears in history
      await waitFor(element(by.id('incident-item-0')))
        .toBeVisible()
        .withTimeout(3000);

      // Verify incident details
      await detoxExpect(element(by.id('incident-sentiment-0'))).toBeVisible();
      await detoxExpect(element(by.id('incident-timestamp-0'))).toBeVisible();
    });

    it('should persist session after app reload', async () => {
      // Complete a recording flow
      await element(by.text('Guest User')).tap();
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // Reload app
      await device.reloadReactNative();

      // Verify still authenticated
      await waitFor(element(by.text('Welcome back!')))
        .toBeVisible()
        .withTimeout(3000);

      // Verify history persisted
      await element(by.id('tab-history')).tap();
      await waitFor(element(by.id('incident-item-0')))
        .toBeVisible()
        .withTimeout(3000);
    });
  });

  describe('Google User Complete Flow', () => {
    it('should complete journey with Google authentication', async () => {
      // Note: This test requires mocking Google Sign-In in E2E environment
      // For actual E2E, this would trigger real OAuth flow

      // Step 1: Attempt Google login (will be mocked in test environment)
      await waitFor(element(by.text('Google Login')))
        .toBeVisible()
        .withTimeout(5000);

      await element(by.text('Google Login')).tap();

      // In real E2E, user would complete OAuth flow
      // In mocked environment, proceed directly

      await waitFor(element(by.text('Welcome back!')))
        .toBeVisible()
        .withTimeout(10000); // Allow time for OAuth

      // Continue with recording flow...
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);
    });
  });

  describe('Navigation Flow', () => {
    it('should navigate between all tabs correctly', async () => {
      await element(by.text('Guest User')).tap();

      // Test each tab
      await element(by.id('tab-home')).tap();
      await waitFor(element(by.id('home-screen')))
        .toBeVisible()
        .withTimeout(2000);

      await element(by.id('tab-recording')).tap();
      await waitFor(element(by.id('recording-screen')))
        .toBeVisible()
        .withTimeout(2000);

      await element(by.id('tab-meditation')).tap();
      await waitFor(element(by.id('meditation-screen')))
        .toBeVisible()
        .withTimeout(2000);

      await element(by.id('tab-history')).tap();
      await waitFor(element(by.id('history-screen')))
        .toBeVisible()
        .withTimeout(2000);
    });

    it('should maintain state when navigating between tabs', async () => {
      await element(by.text('Guest User')).tap();

      // Start recording
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();

      // Navigate away
      await element(by.id('tab-history')).tap();

      // Navigate back
      await element(by.id('tab-recording')).tap();

      // Recording should still be active
      await detoxExpect(element(by.id('recording-status'))).toHaveText('Recording...');
    });
  });

  describe('Multi-Recording Flow', () => {
    it('should handle multiple recordings in sequence', async () => {
      await element(by.text('Guest User')).tap();
      await element(by.id('tab-recording')).tap();

      // First recording
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await element(by.id('stop-button')).tap();
      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // Second recording
      await element(by.id('new-recording-button')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await element(by.id('stop-button')).tap();
      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify history has both recordings
      await element(by.id('tab-history')).tap();
      await detoxExpect(element(by.id('incident-item-0'))).toBeVisible();
      await detoxExpect(element(by.id('incident-item-1'))).toBeVisible();
    });
  });

  describe('Meditation Playback Flow', () => {
    it('should play, pause, and stop meditation correctly', async () => {
      await element(by.text('Guest User')).tap();
      await element(by.id('tab-recording')).tap();

      // Complete recording and get meditation
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();
      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      await element(by.id('generate-meditation-button')).tap();
      await waitFor(element(by.id('meditation-ready')))
        .toBeVisible()
        .withTimeout(30000);

      // Play
      await element(by.id('play-meditation-button')).tap();
      await waitFor(element(by.id('playback-status')))
        .toHaveText('Playing')
        .withTimeout(2000);

      // Pause
      await element(by.id('pause-meditation-button')).tap();
      await waitFor(element(by.id('playback-status')))
        .toHaveText('Paused')
        .withTimeout(2000);

      // Resume
      await element(by.id('play-meditation-button')).tap();
      await waitFor(element(by.id('playback-status')))
        .toHaveText('Playing')
        .withTimeout(2000);

      // Stop
      await element(by.id('stop-meditation-button')).tap();
      await waitFor(element(by.id('playback-status')))
        .toHaveText('Stopped')
        .withTimeout(2000);
    });
  });

  describe('History Interaction Flow', () => {
    it('should view incident details from history', async () => {
      await element(by.text('Guest User')).tap();

      // Create an incident
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();
      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // View in history
      await element(by.id('tab-history')).tap();
      await waitFor(element(by.id('incident-item-0')))
        .toBeVisible()
        .withTimeout(3000);

      // Tap to view details
      await element(by.id('incident-item-0')).tap();

      // Verify details screen
      await waitFor(element(by.id('incident-detail-screen')))
        .toBeVisible()
        .withTimeout(2000);

      await detoxExpect(element(by.id('detail-sentiment'))).toBeVisible();
      await detoxExpect(element(by.id('detail-summary'))).toBeVisible();
      await detoxExpect(element(by.id('detail-transcript'))).toBeVisible();
    });

    it('should delete incident from history', async () => {
      await element(by.text('Guest User')).tap();

      // Create an incident
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();
      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // Go to history
      await element(by.id('tab-history')).tap();
      await waitFor(element(by.id('incident-item-0')))
        .toBeVisible()
        .withTimeout(3000);

      // Delete incident
      await element(by.id('delete-incident-0')).tap();

      // Confirm deletion
      await element(by.text('Delete')).tap();

      // Verify incident removed
      await waitFor(element(by.id('incident-item-0')))
        .not.toBeVisible()
        .withTimeout(2000);
    });
  });

  describe('Sign Out Flow', () => {
    it('should sign out and clear session data', async () => {
      await element(by.text('Guest User')).tap();

      // Create some data
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();
      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // Navigate to profile/settings
      await element(by.id('tab-profile')).tap();

      // Sign out
      await element(by.id('sign-out-button')).tap();

      // Confirm sign out
      await element(by.text('Sign Out')).tap();

      // Verify back at auth screen
      await waitFor(element(by.text('Guest User')))
        .toBeVisible()
        .withTimeout(3000);

      // Sign back in and verify history is cleared
      await element(by.text('Guest User')).tap();
      await element(by.id('tab-history')).tap();

      // History should be empty
      await waitFor(element(by.id('empty-history-message')))
        .toBeVisible()
        .withTimeout(3000);
    });
  });
});
