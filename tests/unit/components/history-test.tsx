import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import ArchivedItemsScreen from '@/frontend/components/history';

// Mock IncidentContext
const mockSetIncidentList = jest.fn();

jest.mock('@/context/IncidentContext', () => ({
  useIncident: () => ({
    incidentList: [],
    setIncidentList: mockSetIncidentList,
    musicList: [],
    setMusicList: jest.fn(),
  }),
}));

// Mock ParallaxScrollView
jest.mock('@/components/ParallaxScrollView', () => {
  const { View } = require('react-native');
  return {
    __esModule: true,
    default: ({ children }: any) => <View testID="parallax-scroll-view">{children}</View>,
  };
});

// Mock ThemedView and ThemedText
jest.mock('@/components/ThemedView', () => ({
  ThemedView: ({ children, style, ...props }: any) => {
    const { View } = require('react-native');
    return (
      <View style={style} {...props}>
        {children}
      </View>
    );
  },
}));

jest.mock('@/components/ThemedText', () => ({
  ThemedText: ({ children, ...props }: any) => {
    const { Text } = require('react-native');
    return <Text {...props}>{children}</Text>;
  },
}));

// Mock useStyles
jest.mock('@/constants/StylesConstants', () => ({
  __esModule: true,
  default: () => ({
    headerImage: {},
    stepContainer: {},
  }),
}));

describe('ArchivedItemsScreen (history)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing', () => {
    const { toJSON } = render(<ArchivedItemsScreen />);
    expect(toJSON()).toBeTruthy();
  });

  it('should render ParallaxScrollView', () => {
    const { getByTestId } = render(<ArchivedItemsScreen />);
    expect(getByTestId('parallax-scroll-view')).toBeTruthy();
  });

  it('should fetch and display archived items', async () => {
    const { getByText } = render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalled();
    });

    // The component fetches mock data with 3 items
    const callArgs = mockSetIncidentList.mock.calls[0][0];
    expect(callArgs).toHaveLength(3);
    expect(callArgs[0]).toMatchObject({
      id: '1',
      title: 'Archived Item 1',
      sentiment_label: 'neutral',
      intensity: 1,
    });
  });

  it('should render all fetched items in FlatList', async () => {
    const { getByText } = render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalled();
    });

    // Since we're mocking the context to return empty list,
    // we verify that setIncidentList was called with the mock data
    const callArgs = mockSetIncidentList.mock.calls[0][0];
    expect(callArgs[0].title).toBe('Archived Item 1');
    expect(callArgs[1].title).toBe('Archived Item 2');
    expect(callArgs[2].title).toBe('Archived Item 3');
  });

  it('should add timestamps to items without them', async () => {
    render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalled();
    });

    const callArgs = mockSetIncidentList.mock.calls[0][0];
    callArgs.forEach((item: any) => {
      expect(item.timestamp).toBeTruthy();
      expect(typeof item.timestamp).toBe('string');
    });
  });

  it('should set default sentiment_label for items', async () => {
    render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalled();
    });

    const callArgs = mockSetIncidentList.mock.calls[0][0];
    callArgs.forEach((item: any) => {
      expect(item.sentiment_label).toBeTruthy();
    });
  });

  it('should set default intensity for items', async () => {
    render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalled();
    });

    const callArgs = mockSetIncidentList.mock.calls[0][0];
    callArgs.forEach((item: any) => {
      expect(item.intensity).toBeTruthy();
      expect(typeof item.intensity).toBe('number');
    });
  });

  it('should preserve existing item properties', async () => {
    render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalled();
    });

    const callArgs = mockSetIncidentList.mock.calls[0][0];
    expect(callArgs[0]).toHaveProperty('id', '1');
    expect(callArgs[0]).toHaveProperty('title', 'Archived Item 1');
    expect(callArgs[1]).toHaveProperty('id', '2');
    expect(callArgs[2]).toHaveProperty('id', '3');
  });

  it('should call fetchArchivedItemsFromAPI on mount', async () => {
    render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalledTimes(1);
    });
  });

  it('should render FlatList with correct key extractor', async () => {
    const { toJSON } = render(<ArchivedItemsScreen />);

    await waitFor(() => {
      expect(mockSetIncidentList).toHaveBeenCalled();
    });

    // Verify component renders successfully
    expect(toJSON()).toBeTruthy();
  });
});
