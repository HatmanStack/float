/**
 * Error Scenarios E2E Tests
 *
 * These tests verify error handling and recovery flows
 * for common failure scenarios.
 *
 * @requires Detox configured and app built
 * @requires Network mocking capability
 */

import { by, device, element, expect as detoxExpect, waitFor } from 'detox';

describe('Error Scenarios', () => {
  beforeAll(async () => {
    await device.launchApp({
      newInstance: true,
      permissions: { notifications: 'YES', microphone: 'YES' },
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    // Sign in as guest for all error tests
    await waitFor(element(by.text('Guest User')))
      .toBeVisible()
      .withTimeout(5000);
    await element(by.text('Guest User')).tap();
  });

  describe('Network Error Scenarios', () => {
    it('should handle network timeout during summary generation', async () => {
      // Note: This requires network mocking in E2E environment
      // Use Detox's network synchronization or mock server

      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      // Simulate network timeout by waiting for error
      await waitFor(element(by.id('error-message')))
        .toBeVisible()
        .withTimeout(60000); // Allow time for timeout

      // Verify error message
      await detoxExpect(element(by.id('error-message'))).toHaveText(
        /network|timeout|connection/i as any
      );

      // Verify retry button available
      await detoxExpect(element(by.id('retry-button'))).toBeVisible();
    });

    it('should retry failed summary request', async () => {
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      // Wait for potential error
      await waitFor(element(by.id('error-message')))
        .toBeVisible()
        .withTimeout(60000);

      // Tap retry
      await element(by.id('retry-button')).tap();

      // Should attempt request again
      await waitFor(element(by.id('processing-indicator')))
        .toBeVisible()
        .withTimeout(2000);

      // Either succeeds or shows error again
      const summaryVisible = await (element(by.id('summary-result')) as any).isVisible();
      const errorVisible = await (element(by.id('error-message')) as any).isVisible();

      if (!summaryVisible && !errorVisible) {
        throw new Error('Neither summary nor error displayed after retry');
      }
    });

    it('should handle offline mode gracefully', async () => {
      // Disable network (requires Detox network control)
      // await device.disableNetwork(); // Not available in all Detox versions

      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      // Should show offline error
      await waitFor(element(by.id('error-message')))
        .toBeVisible()
        .withTimeout(30000);

      await detoxExpect(element(by.id('error-message'))).toHaveText(/offline|network/i as any);

      // Verify recording saved locally for later sync
      await element(by.id('tab-history')).tap();
      await waitFor(element(by.id('pending-sync-indicator')))
        .toBeVisible()
        .withTimeout(2000);
    });
  });

  describe('Permission Error Scenarios', () => {
    it('should handle denied microphone permission', async () => {
      // Relaunch app without microphone permission
      await device.launchApp({
        newInstance: true,
        permissions: { microphone: 'NO' },
      });

      await element(by.text('Guest User')).tap();
      await element(by.id('tab-recording')).tap();

      // Attempt to record
      await element(by.id('record-button')).tap();

      // Should show permission error
      await waitFor(element(by.id('permission-error')))
        .toBeVisible()
        .withTimeout(2000);

      // Verify settings button shown
      await detoxExpect(element(by.id('open-settings-button'))).toBeVisible();
    });

    it('should recover when permission granted after denial', async () => {
      // Relaunch with permissions
      await device.launchApp({
        newInstance: true,
        permissions: { microphone: 'YES' },
      });

      await element(by.text('Guest User')).tap();
      await element(by.id('tab-recording')).tap();

      // Now recording should work
      await element(by.id('record-button')).tap();

      await waitFor(element(by.id('recording-status')))
        .toHaveText('Recording...')
        .withTimeout(2000);
    });
  });

  describe('Backend Error Scenarios', () => {
    it('should handle 500 server error during summary', async () => {
      // Note: Requires backend mocking to return 500

      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      // Wait for error from server
      await waitFor(element(by.id('error-message')))
        .toBeVisible()
        .withTimeout(60000);

      // Verify server error message
      await detoxExpect(element(by.id('error-message'))).toHaveText(/server|error|500/i as any);

      // Verify can dismiss and try again
      await element(by.id('dismiss-error-button')).tap();
      await detoxExpect(element(by.id('record-button'))).toBeVisible();
    });

    it('should handle invalid response from backend', async () => {
      // Note: Requires backend mocking to return malformed JSON

      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      await waitFor(element(by.id('error-message')))
        .toBeVisible()
        .withTimeout(60000);

      // Should show parsing error
      await detoxExpect(element(by.id('error-message'))).toHaveText(/invalid|parse|format/i as any);
    });

    it('should handle meditation generation failure', async () => {
      // First create a summary (assume this works)
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // Try to generate meditation (assume this fails)
      await element(by.id('generate-meditation-button')).tap();

      // Should show error
      await waitFor(element(by.id('meditation-error')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify summary is still displayed (not lost)
      await detoxExpect(element(by.id('summary-result'))).toBeVisible();

      // Verify can retry meditation generation
      await detoxExpect(element(by.id('retry-meditation-button'))).toBeVisible();
    });
  });

  describe('App State Error Scenarios', () => {
    it('should handle app backgrounding during recording', async () => {
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();

      // Verify recording started
      await waitFor(element(by.id('recording-status')))
        .toHaveText('Recording...')
        .withTimeout(2000);

      // Send app to background
      await device.sendToHome();
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Bring back to foreground
      await device.launchApp({ newInstance: false });

      // Should either:
      // 1. Show warning that recording was interrupted
      // 2. Have automatically stopped and saved recording
      const warningVisible = await (element(by.id('recording-interrupted-warning')) as any).isVisible();
      const recordingComplete = await (element(by.id('processing-indicator')) as any).isVisible();

      if (!warningVisible && !recordingComplete) {
        // At minimum, recording should not still show as active
        const statusText = await (element(by.id('recording-status')) as any).getAttributes();
        if ((statusText as any).text === 'Recording...') {
          throw new Error('Recording still active after backgrounding');
        }
      }
    });

    it('should handle app crash recovery', async () => {
      // Create some data
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      await waitFor(element(by.id('summary-result')))
        .toBeVisible()
        .withTimeout(30000);

      // Simulate crash by force-terminating and relaunching
      await device.terminateApp();
      await device.launchApp({ newInstance: false });

      // Should restore to safe state
      await waitFor(element(by.text('Welcome back!')))
        .toBeVisible()
        .withTimeout(5000);

      // Check if data persisted
      await element(by.id('tab-history')).tap();

      // Should either show saved incident or be empty (both are acceptable)
      const hasIncidents = await (element(by.id('incident-item-0')) as any).isVisible();
      const isEmpty = await (element(by.id('empty-history-message')) as any).isVisible();

      if (!hasIncidents && !isEmpty) {
        throw new Error('History screen in unexpected state after crash recovery');
      }
    });
  });

  describe('Data Validation Error Scenarios', () => {
    it('should handle too short recording', async () => {
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();

      // Stop immediately (< 1 second)
      await new Promise((resolve) => setTimeout(resolve, 500));
      await element(by.id('stop-button')).tap();

      // Should show validation error
      await waitFor(element(by.id('validation-error')))
        .toBeVisible()
        .withTimeout(2000);

      await detoxExpect(element(by.id('validation-error'))).toHaveText(/short|minimum|duration/i as any);

      // Should not attempt backend call
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await detoxExpect(element(by.id('processing-indicator'))).not.toBeVisible();
    });

    it('should handle empty/silent audio recording', async () => {
      // Note: This requires microphone mocking to provide silent input

      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      // Backend should return error for silent audio
      await waitFor(element(by.id('error-message')))
        .toBeVisible()
        .withTimeout(30000);

      await detoxExpect(element(by.id('error-message'))).toHaveText(
        /silent|no audio|could not detect/i as any
      );
    });
  });

  describe('Error Recovery Flows', () => {
    it('should clear error state when starting new recording', async () => {
      await element(by.id('tab-recording')).tap();

      // Trigger an error (too short recording)
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 500));
      await element(by.id('stop-button')).tap();

      await waitFor(element(by.id('validation-error')))
        .toBeVisible()
        .withTimeout(2000);

      // Start new recording
      await element(by.id('record-button')).tap();

      // Error should be cleared
      await waitFor(element(by.id('validation-error')))
        .not.toBeVisible()
        .withTimeout(2000);

      // Recording status should show
      await detoxExpect(element(by.id('recording-status'))).toHaveText('Recording...');
    });

    it('should allow cancelling stuck operation', async () => {
      await element(by.id('tab-recording')).tap();
      await element(by.id('record-button')).tap();
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await element(by.id('stop-button')).tap();

      // While processing, cancel button should be available
      await waitFor(element(by.id('processing-indicator')))
        .toBeVisible()
        .withTimeout(2000);

      if (await (element(by.id('cancel-button')) as any).isVisible()) {
        await element(by.id('cancel-button')).tap();

        // Should return to ready state
        await waitFor(element(by.id('record-button')))
          .toBeVisible()
          .withTimeout(2000);
      }
    });
  });
});
