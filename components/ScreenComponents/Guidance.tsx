import React from 'react';
import { ThemedText } from '@/components/ThemedText';
import { Collapsible } from '@/components/Collapsible'; // Assuming these are custom components

const Guidance = () => (
  <Collapsible title="Guidance" incidentColor={{ light: '#fff', dark: '#151718' }}>
    <ThemedText type="body">Tap on the text to view the incident details this selects the incident</ThemedText>
    <ThemedText type="body">You can select up to 3 incidents at a time</ThemedText>
    <ThemedText type="body">Tap on generate to create a personal meditation about the selected incidents</ThemedText>
    <ThemedText type="body">The color change indicates time passage since incident</ThemedText>
    <ThemedText type="body">The green incidents are ready to be dealt with</ThemedText>
  </Collapsible>
);

export default Guidance;