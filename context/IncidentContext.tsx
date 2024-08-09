import React, { createContext, useContext, useState } from 'react';

const IncidentContext = createContext(null);

export const IncidentProvider = ({ children }) => {
  const [incidentList, setIncidentList] = useState([]);
  const [musicList, setMusicList] = useState([]);
  const [colorChangeArrayOfArrays, setColorChangeArrayOfArrays] = useState('#FFFFFF');

  return (
    <IncidentContext.Provider value={{ incidentList, setIncidentList, colorChangeArrayOfArrays, setColorChangeArrayOfArrays, musicList, setMusicList }}>
      {children}
    </IncidentContext.Provider>
  );
};

export const useIncident = () => useContext(IncidentContext);