import React from 'react';
import { Pressable } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { Collapsible } from '@/components/Collapsible';

const IncidentItem = ({ incident, index, selectedIndexes, handlePress, colorChangeSingleArray }) => {
  const timestamp = new Date(incident.timestamp).toLocaleString();
  const displayText = selectedIndexes.includes(index) ? incident.user_summary : `${incident.user_short_summary} - ${timestamp}`;

  return (
    <Pressable onPress={handlePress(index)} key={`${timestamp}-${index}`} style={{ backgroundColor: colorChangeSingleArray[index] || '#FFFFFF', padding: selectedIndexes.includes(index) ? 50 : 30 }}>
      <ThemedText type="body" style={{ color: '#ffffff' }}>
        {displayText}
      </ThemedText>
      {selectedIndexes.includes(index) && 
      <Collapsible title="Details" incidentColor={colorChangeSingleArray[index] || '#FFFFFF'}>
        <ThemedText type="body">Sentiment: {incident.sentiment_label}</ThemedText>
        <ThemedText type="body">Intensity: {incident.intensity}</ThemedText>
        <ThemedText type="body">Reasoning: {incident.summary}</ThemedText>
        {incident.speech_to_text !== 'NotAvailable' && (
          <ThemedText type="body">Speech: {incident.speech_to_text}</ThemedText>
        )}
        {incident.added_text !== 'NotAvailable' && (
          <ThemedText type="body">Text: {incident.added_text}</ThemedText>
        )}
      </Collapsible>}
    </Pressable>
  );
};

export default IncidentItem;