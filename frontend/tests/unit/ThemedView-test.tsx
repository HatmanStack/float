import React from 'react';
import { render } from '@testing-library/react-native';
import { ThemedView } from '@/components/ThemedView';
import { Text } from 'react-native';

// Mock useThemeColor hook
jest.mock('@/hooks/useThemeColor', () => ({
  useThemeColor: jest.fn((colors, colorName) => colors.light || '#fff'),
}));

describe('ThemedView', () => {
  it('should render children correctly', () => {
    const { getByText } = render(
      <ThemedView>
        <Text>Test Content</Text>
      </ThemedView>
    );
    expect(getByText('Test Content')).toBeTruthy();
  });

  it('should apply custom light color', () => {
    const { getByTestId } = render(
      <ThemedView testID="themed-view" lightColor="#ff0000">
        <Text>Content</Text>
      </ThemedView>
    );
    expect(getByTestId('themed-view')).toBeTruthy();
  });

  it('should apply custom dark color', () => {
    const { getByTestId } = render(
      <ThemedView testID="themed-view" darkColor="#000000">
        <Text>Content</Text>
      </ThemedView>
    );
    expect(getByTestId('themed-view')).toBeTruthy();
  });

  it('should apply additional styles', () => {
    const customStyle = { padding: 10, margin: 5 };
    const { getByTestId } = render(
      <ThemedView testID="themed-view" style={customStyle}>
        <Text>Content</Text>
      </ThemedView>
    );
    const view = getByTestId('themed-view');
    expect(view).toBeTruthy();
    expect(view.props.style).toContainEqual(customStyle);
  });

  it('should pass through ViewProps', () => {
    const onLayout = jest.fn();
    const { getByTestId } = render(
      <ThemedView testID="themed-view" onLayout={onLayout} accessible={true}>
        <Text>Content</Text>
      </ThemedView>
    );
    expect(getByTestId('themed-view')).toBeTruthy();
    expect(getByTestId('themed-view').props.accessible).toBe(true);
  });

  it('should render with both light and dark colors specified', () => {
    const { getByTestId } = render(
      <ThemedView testID="themed-view" lightColor="#ffffff" darkColor="#000000">
        <Text>Content</Text>
      </ThemedView>
    );
    expect(getByTestId('themed-view')).toBeTruthy();
  });

  it('should render without custom colors', () => {
    const { getByText } = render(
      <ThemedView>
        <Text>Default Background</Text>
      </ThemedView>
    );
    expect(getByText('Default Background')).toBeTruthy();
  });

  it('should support multiple children', () => {
    const { getByText } = render(
      <ThemedView>
        <Text>Child 1</Text>
        <Text>Child 2</Text>
        <Text>Child 3</Text>
      </ThemedView>
    );
    expect(getByText('Child 1')).toBeTruthy();
    expect(getByText('Child 2')).toBeTruthy();
    expect(getByText('Child 3')).toBeTruthy();
  });
});
