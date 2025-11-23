import { render, waitFor } from '@testing-library/react-native';
import { IncidentColoring } from '@/frontend/components/IncidentColoring';
import { getCurrentTime } from '@/frontend/constants/StylesConstants';
import { IncidentContext, IncidentProvider } from '@/frontend/context/IncidentContext';
import React from 'react';

jest.useFakeTimers();
const mockDateNow = new Date('2023-10-26T12:00:00.000Z');
jest.mock('@/constants/util', () => ({
  getCurrentTime: jest.fn(), // Mock the function
}));

describe('IncidentColoring', () => {
  const mockIncidentList = [
    {
      sentiment_label: 'Happy',
      intensity: '3',
      timestamp: '2023-10-26T11:00:00.000Z',
      color_key: 0,
    },
    {
      sentiment_label: 'Sad',
      intensity: '1',
      timestamp: '2023-10-26T11:30:00.000Z',
      color_key: 0,
    },
    {
      sentiment_label: 'Neutral',
      intensity: '5',
      timestamp: '2023-10-26T10:00:00.000Z',
      color_key: 0,
    },
  ];

  const wrapper = ({ children }) => <IncidentProvider>{children}</IncidentProvider>;

  beforeEach(() => {
    jest.spyOn(global.Date, 'now').mockImplementation(() => mockDateNow.getTime());
    (getCurrentTime as jest.Mock).mockReturnValue(mockDateNow);
  });

  afterEach(() => {
    jest.restoreAllMocks(); // Restore all mocked functions
  });

  it('should render without crashing', () => {
    render(<IncidentColoring />, { wrapper });
  });

  it('should correctly calculate color arrays for incidents', async () => {
    const setColorChangeArrayOfArrays = jest.fn();
    const incidentList = mockIncidentList;

    render(
      <IncidentContext.Provider value={{ incidentList, setColorChangeArrayOfArrays }}>
        <IncidentColoring />
      </IncidentContext.Provider>,
      { wrapper }
    );

    await waitFor(() => {
      expect(setColorChangeArrayOfArrays).toHaveBeenCalledTimes(1);
      expect(setColorChangeArrayOfArrays).toHaveBeenCalledWith(
        expect.arrayContaining([expect.any(Array), expect.any(Array), expect.any(Array)])
      );
    });
  });

  it('should update color key for incidents based on time difference', async () => {
    const setColorChangeArrayOfArrays = jest.fn();

    (getCurrentTime as jest.Mock).mockReturnValue(mockDateNow);
    const incidentList = mockIncidentList;

    render(
      <IncidentContext.Provider
        value={{
          incidentList,
          setColorChangeArrayOfArrays,
          colorChangeArrayOfArrays: '',
          setIncidentList: jest.fn(),
          musicList: [],
          setMusicList: jest.fn(),
        }}
      >
        <IncidentColoring />
      </IncidentContext.Provider>,
      { wrapper }
    );

    // Check if setColorChangeArrayOfArrays was called with color arrays
    await waitFor(() => {
      expect(setColorChangeArrayOfArrays).toHaveBeenCalled();
      const callArg = setColorChangeArrayOfArrays.mock.calls[0][0];
      // Should be called with array of color arrays
      expect(Array.isArray(callArg)).toBe(true);
      expect(callArg.length).toBe(3);
    });
  });
});
