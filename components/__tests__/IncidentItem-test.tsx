import React from 'react';
import { View, TouchableOpacity, Text } from 'react-native';
import { render, screen, fireEvent } from '@testing-library/react-native';
import IncidentItem from '@/components/ScreenComponents/IncidentItem';
import { useIncident } from '@/context/IncidentContext';
import { ThemedText } from '@/components/ThemedText';
import { Collapsible } from '@/components/Collapsible';

// Mock the useIncident hook and its return values
jest.mock('@/context/IncidentContext', () => ({
  useIncident: () => ({
    colorChangeArrayOfArrays: [
      ['#f00', '#f50', '#ff0'], // Example colors for the first incident
    ],
  }),
}));

// Define mock component BEFORE jest.mock to avoid hoisting issues
function MockCollapsible({ children, isOpen, onToggle, ...props }) {
  return (
    <View {...props}>
      <TouchableOpacity onPress={onToggle}>
        <Text>Mock Collapsible - {isOpen ? 'Open' : 'Closed'}</Text>
      </TouchableOpacity>
      {isOpen && <View>{children}</View>}
    </View>
  );
}

// Mock the Collapsible component to avoid unnecessary rendering and logic
jest.mock('@/components/Collapsible', () => {
  return {
    Collapsible: ({ children, ...props }) => (
      <MockCollapsible {...props}>{children}</MockCollapsible>
    ),
  };
});

describe('IncidentItem', () => {
  const mockIncident = {
    sentiment_label: 'Happy',
    intensity: '3',
    timestamp: '2023-12-20T12:00:00.000Z',
    user_summary: 'This is a summary of the incident.',
    user_short_summary: 'Short summary',
    summary: 'Detailed summary',
    speech_to_text: 'Speech to text content',
    added_text: 'Added text content',
  };

  const mockHandlePress = jest.fn();
  const mockToggleCollapsible = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with basic information', () => {
    render(
      <IncidentItem
        renderKey="testKey"
        incident={mockIncident}
        index={0}
        selectedIndexes={[]}
        handlePress={mockHandlePress}
        isOpen={false}
        toggleCollapsible={mockToggleCollapsible}
      />
    );

    expect(screen.getByText('Short summary - 12/20/2023, 12:00:00 PM')).toBeTruthy();
  });

  it('renders correctly with selected state', () => {
    render(
      <IncidentItem
        renderKey="testKey"
        incident={mockIncident}
        index={0}
        selectedIndexes={[0]} // Mark incident as selected
        handlePress={mockHandlePress}
        isOpen={false}
        toggleCollapsible={mockToggleCollapsible}
      />
    );

    expect(screen.getByText(mockIncident.user_summary)).toBeTruthy();
    expect(screen.getByText('Mock Collapsible - Closed')).toBeTruthy(); // Collapsible should be present
  });

  it('calls handlePress when pressed', () => {
    render(
      <IncidentItem
        renderKey="testKey"
        incident={mockIncident}
        index={0}
        selectedIndexes={[]}
        handlePress={mockHandlePress}
        isOpen={false}
        toggleCollapsible={mockToggleCollapsible}
      />
    );

    fireEvent.press(screen.getByText('Short summary - 12/20/2023, 12:00:00 PM'));
    expect(mockHandlePress).toHaveBeenCalledWith(0);
  });

  it('toggles collapsible content when header is pressed', () => {
    render(
      <IncidentItem
        renderKey="testKey"
        incident={mockIncident}
        index={0}
        selectedIndexes={[0]} // Mark as selected to show collapsible
        handlePress={mockHandlePress}
        isOpen={false}
        toggleCollapsible={mockToggleCollapsible}
      />
    );

    fireEvent.press(screen.getByText('Mock Collapsible - Closed'));
    expect(mockToggleCollapsible).toHaveBeenCalled();
  });
});
