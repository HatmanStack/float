import React from 'react';
import { View, TouchableOpacity, Text } from 'react-native';
import { render, screen, fireEvent } from '@testing-library/react-native';
import Guidance from '@/components/ScreenComponents/Guidance'; // Adjust the path if needed
import { ThemedText } from '@/components/ThemedText'; // Adjust the path if needed
import { Collapsible } from '@/components/Collapsible'; // Adjust the path if needed

interface MockCollapsibleProps {
  children: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
}

// Mock component to simulate behavior
const MockCollapsible = ({ children, isOpen, onToggle }: MockCollapsibleProps) => (
  <View>
    <TouchableOpacity onPress={onToggle}>
      <Text>Mock Collapsible - {isOpen ? 'Open' : 'Closed'}</Text>
    </TouchableOpacity>
    {isOpen && <View>{children}</View>}
  </View>
);

// Mock the Collapsible component to avoid unnecessary rendering and logic
jest.mock('@/components/Collapsible', () => {
  return {
    Collapsible: ({ children, ...props }: { children: React.ReactNode; isOpen: boolean; onToggle: () => void }) => (
      <MockCollapsible {...props}>{children}</MockCollapsible>
    ),
  };
});

describe('Guidance', () => {
  it('renders correctly', () => {
    render(<Guidance />);
    expect(screen.getByText('Mock Collapsible - Closed')).toBeTruthy();
  });

  it('toggles the collapsible content on press', () => {
    render(<Guidance />);

    // Initially, the content should be closed
    expect(
      screen.queryByText('Tap on the text to view the float details this selects the float')
    ).toBeNull();

    // Fire a press event on the collapsible header
    fireEvent.press(screen.getByText('Mock Collapsible - Closed'));

    // The content should now be open
    expect(screen.getByText('Mock Collapsible - Open')).toBeTruthy();
    expect(
      screen.getByText('Tap on the text to view the float details this selects the float')
    ).toBeTruthy();
  });
});
