import React, { createContext, useContext, useState, ReactNode } from 'react';

/** Intensity level from sentiment analysis (1=lowest, 5=highest) */
type IntensityLevel = 1 | 2 | 3 | 4 | 5;

export interface Incident {
  id?: string;
  timestamp: string | number | Date;
  sentiment_label: string;
  /** Intensity 1-5. May arrive as string from API, normalize with parseInt. */
  intensity: IntensityLevel | number;
  user_summary?: string;
  user_short_summary?: string;
  summary?: string;
  speech_to_text?: string;
  added_text?: string;
  [key: string]: string | number | boolean | Date | undefined;
}

export interface IncidentContextType {
  incidentList: Incident[];
  setIncidentList: React.Dispatch<React.SetStateAction<Incident[]>>;
  colorChangeArrayOfArrays: string | string[][];
  setColorChangeArrayOfArrays: React.Dispatch<React.SetStateAction<string | string[][]>>;
  musicList: string[];
  setMusicList: React.Dispatch<React.SetStateAction<string[]>>;
}

export const IncidentContext = createContext<IncidentContextType | null>(null);

export const IncidentProvider = ({ children }: { children: ReactNode }) => {
  const [incidentList, setIncidentList] = useState<Incident[]>([]);
  const [musicList, setMusicList] = useState<string[]>([]);
  const [colorChangeArrayOfArrays, setColorChangeArrayOfArrays] = useState<string | string[][]>(
    '#FFFFFF'
  );

  return (
    <IncidentContext.Provider
      value={{
        incidentList,
        setIncidentList,
        colorChangeArrayOfArrays,
        setColorChangeArrayOfArrays,
        musicList,
        setMusicList,
      }}
    >
      {children}
    </IncidentContext.Provider>
  );
};

export const useIncident = (): IncidentContextType => {
  const context = useContext(IncidentContext);
  if (!context) {
    throw new Error('useIncident must be used within IncidentProvider');
  }
  return context;
};
