import React from 'react';
import { render } from '@testing-library/react-native';
import { Text, View } from 'react-native';
import ParallaxScrollView from '@/components/ParallaxScrollView';

// Mock ThemedView
jest.mock('@/components/ThemedView', () => ({
  ThemedView: ({ children, style, ...props }: any) => {
    const { View } = require('react-native');
    return <View style={style} {...props}>{children}</View>;
  },
}));

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const React = require('react');
  const { View, ScrollView } = require('react-native');

  return {
    __esModule: true,
    default: {
      View: View,
      ScrollView: ScrollView,
      createAnimatedComponent: (Component: any) => Component,
    },
    useAnimatedRef: () => ({ current: null }),
    useAnimatedStyle: () => ({}),
    useScrollViewOffset: () => ({ value: 0 }),
    interpolate: () => 0,
  };
});

describe('ParallaxScrollView', () => {
  const mockHeaderImage = <Text>Header Image</Text>;
  const mockHeaderText = <Text>Header Text</Text>;
  const mockHeaderBackgroundColor = { dark: '#000', light: '#fff' };

  it('should render children correctly', () => {
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={mockHeaderText}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Test Content</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Test Content')).toBeTruthy();
  });

  it('should render header image', () => {
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={mockHeaderText}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Content</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Header Image')).toBeTruthy();
  });

  it('should render header text', () => {
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={mockHeaderText}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Content</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Header Text')).toBeTruthy();
  });

  it('should render with custom header image', () => {
    const customHeaderImage = <Text>Custom Header</Text>;
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={customHeaderImage}
        headerText={mockHeaderText}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Content</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Custom Header')).toBeTruthy();
  });

  it('should render with custom header text', () => {
    const customHeaderText = <Text>Welcome to App</Text>;
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={customHeaderText}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Content</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Welcome to App')).toBeTruthy();
  });

  it('should render multiple children', () => {
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={mockHeaderText}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Child 1</Text>
        <Text>Child 2</Text>
        <Text>Child 3</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Child 1')).toBeTruthy();
    expect(getByText('Child 2')).toBeTruthy();
    expect(getByText('Child 3')).toBeTruthy();
  });

  it('should apply header background color for light mode', () => {
    const customColors = { light: '#ffffff', dark: '#000000' };
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={mockHeaderText}
        headerBackgroundColor={customColors}
      >
        <Text>Content</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Header Image')).toBeTruthy();
  });

  it('should render with complex header content', () => {
    const complexHeader = (
      <View>
        <Text>Title</Text>
        <Text>Subtitle</Text>
      </View>
    );
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={complexHeader}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Body Content</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Title')).toBeTruthy();
    expect(getByText('Subtitle')).toBeTruthy();
    expect(getByText('Body Content')).toBeTruthy();
  });

  it('should render scrollable content area', () => {
    const { getByText } = render(
      <ParallaxScrollView
        headerImage={mockHeaderImage}
        headerText={mockHeaderText}
        headerBackgroundColor={mockHeaderBackgroundColor}
      >
        <Text>Scrollable Item 1</Text>
        <Text>Scrollable Item 2</Text>
      </ParallaxScrollView>
    );
    expect(getByText('Scrollable Item 1')).toBeTruthy();
    expect(getByText('Scrollable Item 2')).toBeTruthy();
  });
});
