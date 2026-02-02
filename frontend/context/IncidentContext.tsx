import React, { createContext, useContext, useState, ReactNode } from 'react';

/** Intensity level from sentiment analysis (1=lowest, 5=highest) */
export type IntensityLevel = 1 | 2 | 3 | 4 | 5;

/** Valid sentiment labels returned by the AI service */
export type SentimentLabel =
  | 'Angry'
  | 'Disgusted'
  | 'Fearful'
  | 'Happy'
  | 'Neutral'
  | 'Sad'
  | 'Surprised';

/**
 * Incident data structure representing a user's emotional event.
 * All fields are explicitly typed - no permissive index signature.
 */
export interface Incident {
  /** Unique identifier for the incident */
  id?: string;
  /** When the incident was recorded */
  timestamp: string | number | Date;
  /** AI-determined sentiment classification */
  sentiment_label: SentimentLabel | string; // string fallback for API compatibility
  /** Intensity 1-5. May arrive as string from API, normalize with parseInt. */
  intensity: IntensityLevel | number;
  /** First-person summary for user reference */
  user_summary?: string;
  /** Brief description (few words) */
  user_short_summary?: string;
  /** AI's reasoning for sentiment classification */
  summary?: string;
  /** Transcribed text from audio input */
  speech_to_text?: string;
  /** User-provided text input */
  added_text?: string;
  /** Notification ID for scheduled reminders */
  notificationId?: string;
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
