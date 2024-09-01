import { render, waitFor } from "@testing-library/react-native";
import { IncidentColoring } from "@/components/IncidentColoring";
import { getCurrentTime } from '@/constants/util';
import { IncidentContext, IncidentProvider } from "@/context/IncidentContext";
import React from "react";


jest.useFakeTimers();
const mockDateNow = new Date("2023-10-26T12:00:00.000Z");
jest.mock('@/constants/util', () => ({
  getCurrentTime: jest.fn(), // Mock the function
}));

describe("IncidentColoring", () => {  
  const mockIncidentList = [
    {
      sentiment_label: "Happy",
      intensity: "3",
      timestamp: "2023-10-26T11:00:00.000Z", 
      color_key: 0,
    },
    {
      sentiment_label: "Sad",
      intensity: "1",
      timestamp: "2023-10-26T11:30:00.000Z", 
      color_key: 0,
    },
    {
      sentiment_label: "Neutral",
      intensity: "5",
      timestamp: "2023-10-26T10:00:00.000Z", 
      color_key: 0,
    },
  ];

  const wrapper = ({ children }) => (
    <IncidentProvider>{children}</IncidentProvider>
  );
  
  beforeEach(() => {
    jest.spyOn(global.Date, 'now').mockImplementation(() => mockDateNow.getTime());
    (getCurrentTime as jest.Mock).mockReturnValue(mockDateNow);
  });

  afterEach(() => {
    jest.restoreAllMocks(); // Restore all mocked functions
  });

  it("should render without crashing", () => {
    render(<IncidentColoring />, { wrapper });
  });

  it("should correctly calculate color arrays for incidents", async () => {
    const setColorChangeArrayOfArrays = jest.fn();
    const incidentList = mockIncidentList;

    render(
      <IncidentContext.Provider
        value={{ incidentList, setColorChangeArrayOfArrays }}
      >
        <IncidentColoring />
      </IncidentContext.Provider>,
      { wrapper }
    );

    await waitFor(() => {
      expect(setColorChangeArrayOfArrays).toHaveBeenCalledTimes(1);    
      expect(setColorChangeArrayOfArrays).toHaveBeenCalledWith(expect.arrayContaining([
        expect.any(Array), 
          expect.any(Array), 
          expect.any(Array)
      ]));
    });

  });

  it("should update color key for incidents based on time difference", async () => {
    const setColorChangeArrayOfArrays = jest.fn();
    
    (getCurrentTime as jest.Mock).mockReturnValue(mockDateNow);
    const incidentList = mockIncidentList;

    render(
      <IncidentContext.Provider
        value={{ incidentList, setColorChangeArrayOfArrays }}
      >
        <IncidentColoring />
      </IncidentContext.Provider>,
      { wrapper }
    );
    
    // Check if color keys are updated
    expect(incidentList[0].color_key).toBe(4);
    expect(incidentList[1].color_key).toBe(2);
    expect(incidentList[2].color_key).toBe(8);
  });
});
