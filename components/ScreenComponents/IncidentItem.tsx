import React, { useEffect, useRef, useState } from 'react';
import { Animated, Pressable } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { Collapsible } from '@/components/Collapsible';
import { ThemedView } from '@/components/ThemedView';
import { useIncident } from '@/context/IncidentContext';
    

const IncidentItem = ({ renderKey, incident, index, selectedIndexes, handlePress, isOpen, toggleCollapsible }) => {
  const timestamp = new Date(incident.timestamp).toLocaleString();
  const { colorChangeArrayOfArrays } = useIncident();
  const displayText = selectedIndexes.includes(index) ? incident.user_summary : `${incident.user_short_summary} - ${timestamp}`;
  const [isSwiping, setIsSwiping] = useState(false);
  const [colors, setColors] = useState(['#fff', '#fff']);
  const colorAnim = useRef(new Animated.Value(0)).current;
  const colorChangeDuration = 500;
  
  useEffect(() => {
    if (!colorChangeArrayOfArrays || !colorChangeArrayOfArrays[index]) {
      return;
    }
    setColors(colorChangeArrayOfArrays[index]);
  }, [colorChangeArrayOfArrays, index]);

  useEffect(() => {
    const forwardAnimations = colors.map((_, i) => 
      Animated.timing(colorAnim, {
        toValue: i,
        duration: colorChangeDuration,
        useNativeDriver: false,
      })
    );
  
    const reverseAnimations = colors.map((_, i) => 
      Animated.timing(colorAnim, {
        toValue: colors.length - 1 - i,
        duration: colorChangeDuration,
        useNativeDriver: false,
      })
    );
  
    const animationSequence = Animated.sequence([
      ...forwardAnimations,
      ...reverseAnimations,
    ]);
  
    const animationLoop = Animated.loop(animationSequence);
  
    if (!isSwiping) {
      animationLoop.start();
    } else {
      animationLoop.stop();
    }
  }, [colorAnim, colors, isSwiping]);

  const backgroundColor = colorAnim.interpolate({
    inputRange: colors.map((_, i) => i),
    outputRange: colors,
  });

  return (
    <ThemedView style={{flexDirection: "row", justifyContent:"space-between" }}>
    <Animated.View style={{backgroundColor, width: '100%'}}>
    <Pressable 
      onPress={handlePress(index)} 
      onPressIn={() => setIsSwiping(true)}
      onPressOut={() => setIsSwiping(false)}
      key={renderKey + 'selectedIndex'} 
      style={{ 
        padding: selectedIndexes.includes(index) ? 50 : 30
        }}>
      <ThemedText type="details" style={{ color: '#ffffff' }}>
        {displayText}
      </ThemedText>
      
      {selectedIndexes.includes(index) && 
      <Collapsible 
        title="Details" 
        incidentColor={backgroundColor}
        isOpen={isOpen} 
        onToggle={toggleCollapsible}
      >
        <ThemedText type="subtitle">Sentiment: <ThemedText type="details">{incident.sentiment_label}</ThemedText></ThemedText>
        <ThemedText type="subtitle">Intensity: <ThemedText type="details">{incident.intensity}</ThemedText></ThemedText>
        <ThemedText type="subtitle">Reasoning: <ThemedText type="details">{incident.summary}</ThemedText></ThemedText>
        {incident.speech_to_text !== 'NotAvailable' && (
          <ThemedText type="subtitle">Speech: <ThemedText type="details">{incident.speech_to_text}</ThemedText></ThemedText>
        )}
        {incident.added_text !== 'NotAvailable' && (
          <ThemedText type="subtitle">Text: <ThemedText type="details">{incident.added_text}</ThemedText></ThemedText>
        )}
      </Collapsible>}
    </Pressable>
        </Animated.View>
    </ThemedView>
    
  );
};

export default IncidentItem;