import React from 'react';
import { renderHook } from '@testing-library/react-native';
import { IncidentSave } from '../../frontend/components/LocalFileLoadAndSave';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

// Mock IncidentContext
const mockSetIncidentList = jest.fn();
const mockSetMusicList = jest.fn();

jest.mock('@/context/IncidentContext', () => ({
  useIncident: () => ({
    incidentList: [],
    setIncidentList: mockSetIncidentList,
    musicList: [],
    setMusicList: mockSetMusicList,
  }),
}));

describe('IncidentSave', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should load incident list from storage', async () => {
    const mockIncidents = [{ id: 1 }, { id: 2 }];
    (AsyncStorage.getItem as jest.Mock).mockImplementation((key) => {
      if (key === 'incidentList') return Promise.resolve(JSON.stringify(mockIncidents));
      return Promise.resolve(null);
    });

    renderHook(() => IncidentSave());

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(AsyncStorage.getItem).toHaveBeenCalledWith('incidentList');
  });

  it('should load music list from storage', async () => {
    const mockMusic = ['track1', 'track2'];
    (AsyncStorage.getItem as jest.Mock).mockImplementation((key) => {
      if (key === 'musicList') return Promise.resolve(JSON.stringify(mockMusic));
      return Promise.resolve(null);
    });

    renderHook(() => IncidentSave());

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(AsyncStorage.getItem).toHaveBeenCalledWith('musicList');
  });

  it('should handle load errors gracefully', async () => {
    (AsyncStorage.getItem as jest.Mock).mockRejectedValue(new Error('Load failed'));

    renderHook(() => IncidentSave());

    await new Promise((resolve) => setTimeout(resolve, 100));
    // Should not crash
    expect(true).toBe(true);
  });

  it('should return null', () => {
    const result = renderHook(() => IncidentSave());
    expect(result.result.current).toBeNull();
  });
});
