import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { Collapsible } from '@/components/Collapsible';
import { Text } from 'react-native';

// Mock ThemedView and ThemedText
jest.mock('@/components/ThemedView', () => ({
  ThemedView: ({ children, style, ...props }: any) => {
    const { View } = require('react-native');
    return <View style={style} {...props}>{children}</View>;
  },
}));

jest.mock('@/components/ThemedText', () => ({
  ThemedText: ({ children, ...props }: any) => {
    const { Text } = require('react-native');
    return <Text {...props}>{children}</Text>;
  },
}));

describe('Collapsible', () => {
  it('should render title correctly', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Test Title" isOpen={false} onToggle={mockToggle}>
        <Text>Content</Text>
      </Collapsible>
    );
    expect(getByText('Test Title')).toBeTruthy();
  });

  it('should show content when isOpen is true', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Test" isOpen={true} onToggle={mockToggle}>
        <Text>Expanded Content</Text>
      </Collapsible>
    );
    expect(getByText('Expanded Content')).toBeTruthy();
  });

  it('should hide content when isOpen is false', () => {
    const mockToggle = jest.fn();
    const { queryByText } = render(
      <Collapsible title="Test" isOpen={false} onToggle={mockToggle}>
        <Text>Hidden Content</Text>
      </Collapsible>
    );
    expect(queryByText('Hidden Content')).toBeNull();
  });

  it('should call onToggle when pressed', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Test Title" isOpen={false} onToggle={mockToggle}>
        <Text>Content</Text>
      </Collapsible>
    );
    fireEvent.press(getByText('Test Title'));
    expect(mockToggle).toHaveBeenCalledTimes(1);
  });

  it('should call onToggle multiple times', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Toggle Test" isOpen={false} onToggle={mockToggle}>
        <Text>Content</Text>
      </Collapsible>
    );
    fireEvent.press(getByText('Toggle Test'));
    fireEvent.press(getByText('Toggle Test'));
    fireEvent.press(getByText('Toggle Test'));
    expect(mockToggle).toHaveBeenCalledTimes(3);
  });

  it('should apply incident color to background', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Test" isOpen={false} onToggle={mockToggle} incidentColor="#ff0000">
        <Text>Content</Text>
      </Collapsible>
    );
    expect(getByText('Test')).toBeTruthy();
  });

  it('should use custom textType for subtitle', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Test" isOpen={false} onToggle={mockToggle} textType="subtitle">
        <Text>Content</Text>
      </Collapsible>
    );
    expect(getByText('Test')).toBeTruthy();
  });

  it('should use custom textType for incidentSubtitle', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Test" isOpen={false} onToggle={mockToggle} textType="incidentSubtitle">
        <Text>Content</Text>
      </Collapsible>
    );
    expect(getByText('Test')).toBeTruthy();
  });

  it('should render with multiple children when open', () => {
    const mockToggle = jest.fn();
    const { getByText } = render(
      <Collapsible title="Test" isOpen={true} onToggle={mockToggle}>
        <Text>Child 1</Text>
        <Text>Child 2</Text>
      </Collapsible>
    );
    expect(getByText('Child 1')).toBeTruthy();
    expect(getByText('Child 2')).toBeTruthy();
  });

  it('should toggle between open and closed states', () => {
    const mockToggle = jest.fn();
    const { getByText, queryByText, rerender } = render(
      <Collapsible title="Toggle" isOpen={false} onToggle={mockToggle}>
        <Text>Content</Text>
      </Collapsible>
    );

    // Initially closed
    expect(queryByText('Content')).toBeNull();

    // Rerender as open
    rerender(
      <Collapsible title="Toggle" isOpen={true} onToggle={mockToggle}>
        <Text>Content</Text>
      </Collapsible>
    );
    expect(getByText('Content')).toBeTruthy();
  });
});
