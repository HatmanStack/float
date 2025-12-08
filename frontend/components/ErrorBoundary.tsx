/**
 * ErrorBoundary - React error boundary for catching unexpected errors
 * Wraps HLS streaming components to gracefully handle errors
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';
import { Pressable } from 'react-native';
import { Colors } from '@/constants/Colors';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary component for catching and displaying errors in child components.
 * Provides a default fallback UI with retry functionality.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ThemedView style={{ padding: 20, alignItems: 'center' }} testID="error-boundary-fallback">
          <ThemedText type="default" style={{ textAlign: 'center', marginBottom: 10 }}>
            Something went wrong
          </ThemedText>
          <ThemedText type="default" style={{ textAlign: 'center', marginBottom: 20, opacity: 0.7 }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </ThemedText>
          <Pressable
            onPress={this.handleReset}
            style={({ pressed }) => ({
              backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
              paddingHorizontal: 20,
              paddingVertical: 10,
              borderRadius: 8,
            })}
            testID="error-boundary-retry-button"
          >
            <ThemedText type="generate">Try Again</ThemedText>
          </Pressable>
        </ThemedView>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
