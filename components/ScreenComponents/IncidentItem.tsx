import React, { useEffect, useRef, useState } from 'react';
import { Animated, Pressable, Platform } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { Collapsible } from '@/components/Collapsible';
import { ThemedView } from '@/components/ThemedView';
import { useIncident } from '@/context/IncidentContext';
import useStyles from "@/constants/StylesConstants";

    

const IncidentItem = ({ renderKey, incident, index, selectedIndexes, handlePress, isOpen, toggleCollapsible }) => {
  const timestamp = new Date(incident.timestamp).toLocaleString();
  const { colorChangeArrayOfArrays } = useIncident();
  const displayText = selectedIndexes.includes(index) ? incident.user_summary : `${incident.user_short_summary} - ${timestamp}`;
  const [isSwiping, setIsSwiping] = useState(false);
  const styles = useStyles();
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

  const onPressHandler = (index) => {
    console.log("onPressHandler", index);
    handlePress(index)(); // Call the returned function
  };

  return (
    <ThemedView style={styles.incidentContainer}>
    <Animated.View style={{backgroundColor, width: '100%'}}>
    <Pressable 
      onPress={() => onPressHandler(index)} 
      onPressIn={() => setIsSwiping(true)}
      onPressOut={() => setIsSwiping(false)}
      key={renderKey + 'selectedIndex'} 
      style={{ 
        padding: 30,
        paddingTop: selectedIndexes.includes(index) ? 50 : 30,
        paddingBottom: selectedIndexes.includes(index) ? 50 : 30,
        }}>
      <ThemedText type="details" style={{ color: '#ffffff' }}>
        {displayText}
      </ThemedText>
      
      {selectedIndexes.includes(index) && 
      <Collapsible 
        title="Details"
        textType="incidentSubtitle"
        /**{Web Build : incidentColor={backgroundColor} }*/
        isOpen={isOpen}
        onToggle={toggleCollapsible}
      >
        <ThemedText type="incidentSubtitle">Sentiment: <ThemedText type="incidentDetails">{incident.sentiment_label}</ThemedText></ThemedText>
        <ThemedText type="incidentSubtitle">Intensity: <ThemedText type="incidentDetails">{incident.intensity}</ThemedText></ThemedText>
        <ThemedText type="incidentSubtitle">Reasoning: <ThemedText type="incidentDetails">{incident.summary}</ThemedText></ThemedText>
        {incident.speech_to_text !== 'NotAvailable' && (
          <ThemedText type="incidentSubtitle">Speech: <ThemedText type="incidentDetails">{incident.speech_to_text}</ThemedText></ThemedText>
        )}
        {incident.added_text !== 'NotAvailable' && (
          <ThemedText type="incidentSubtitle">Text: <ThemedText type="incidentDetails">{incident.added_text}</ThemedText></ThemedText>
        )}
      </Collapsible>
      }
    </Pressable>
        </Animated.View>
    </ThemedView>
    
  );
};

export default IncidentItem;