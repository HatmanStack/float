import React, { createContext, useContext, useState } from 'react';

const IncidentContext = createContext(null);

export const IncidentProvider = ({ children }) => {
  const [incidentList, setIncidentList] = useState([]);
  const [colorChangeSingleArray, setColorChangeSingleArray] = useState('#FFFFFF');

  return (
    <IncidentContext.Provider value={{ incidentList, setIncidentList, colorChangeSingleArray, setColorChangeSingleArray }}>
      {children}
    </IncidentContext.Provider>
  );
};

export const useIncident = () => useContext(IncidentContext);