import React, { useEffect, useRef, useState } from 'react';
import { Animated, Pressable } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { Collapsible } from '@/components/Collapsible';
import { ThemedView } from '@/components/ThemedView';
import { useIncident } from '@/context/IncidentContext';
import useStyles from '@/constants/StylesConstants';

const IncidentItem = ({
  renderKey,
  incident,
  index,
  selectedIndexes,
  handlePress,
  isOpen,
  toggleCollapsible,
}) => {
  const timestamp = new Date(incident.timestamp).toLocaleString();
  const { colorChangeArrayOfArrays } = useIncident();
  const displayText = selectedIndexes.includes(index)
    ? incident.user_summary
    : `${incident.user_short_summary} - ${timestamp}`;
  const [isSwiping, setIsSwiping] = useState(false);
  const styles = useStyles();
  const colors =
    colorChangeArrayOfArrays?.[index]?.length >= 2
      ? colorChangeArrayOfArrays[index]
      : ['#fff', '#fff'];
  const colorAnim = useRef(new Animated.Value(0));
  const [backgroundColor, setBackgroundColor] = useState('#fff');
  const [staticBackgroundColor, setStaticBackgroundColor] = useState(colors[0] || '#fff');
  const colorChangeDuration = 500;

  useEffect(() => {
    const animValue = colorAnim.current.interpolate({
      inputRange: colors.map((_, i) => i),
      outputRange: colors,
    });
    setBackgroundColor(animValue);
    // Set static color for non-animated components
    setStaticBackgroundColor(colors[0] || '#fff');

    const forwardAnimations = colors.map((_, i) =>
      Animated.timing(colorAnim.current, {
        toValue: i,
        duration: colorChangeDuration,
        useNativeDriver: false,
      })
    );

    const reverseAnimations = colors.map((_, i) =>
      Animated.timing(colorAnim.current, {
        toValue: colors.length - 1 - i,
        duration: colorChangeDuration,
        useNativeDriver: false,
      })
    );

    const animationSequence = Animated.sequence([...forwardAnimations, ...reverseAnimations]);

    const animationLoop = Animated.loop(animationSequence);

    if (!isSwiping) {
      animationLoop.start();
    } else {
      animationLoop.stop();
    }
  }, [colors, isSwiping, colorChangeDuration]);

  const onPressHandler = (index) => {
    console.log('onPressHandler', index);
    handlePress(index)(); // Call the returned function
  };

  return (
    <ThemedView style={styles.incidentContainer}>
      <Animated.View style={{ backgroundColor, width: '100%' }}>
        <Pressable
          onPress={() => onPressHandler(index)}
          onPressIn={() => setIsSwiping(true)}
          onPressOut={() => setIsSwiping(false)}
          key={renderKey + 'selectedIndex'}
          style={{
            padding: 30,
            paddingTop: selectedIndexes.includes(index) ? 50 : 30,
            paddingBottom: selectedIndexes.includes(index) ? 50 : 30,
          }}
        >
          <ThemedText type="details" style={{ color: '#ffffff' }}>
            {displayText}
          </ThemedText>

          {selectedIndexes.includes(index) && (
            <Collapsible
              title="Details"
              textType="incidentSubtitle"
              incidentColor={staticBackgroundColor}
              isOpen={isOpen}
              onToggle={toggleCollapsible}
            >
              <ThemedText type="incidentSubtitle">
                Sentiment:{' '}
                <ThemedText type="incidentDetails">{incident.sentiment_label}</ThemedText>
              </ThemedText>
              <ThemedText type="incidentSubtitle">
                Intensity: <ThemedText type="incidentDetails">{incident.intensity}</ThemedText>
              </ThemedText>
              <ThemedText type="incidentSubtitle">
                Reasoning: <ThemedText type="incidentDetails">{incident.summary}</ThemedText>
              </ThemedText>
              {incident.speech_to_text !== 'NotAvailable' && (
                <ThemedText type="incidentSubtitle">
                  Speech: <ThemedText type="incidentDetails">{incident.speech_to_text}</ThemedText>
                </ThemedText>
              )}
              {incident.added_text !== 'NotAvailable' && (
                <ThemedText type="incidentSubtitle">
                  Text: <ThemedText type="incidentDetails">{incident.added_text}</ThemedText>
                </ThemedText>
              )}
            </Collapsible>
          )}
        </Pressable>
      </Animated.View>
    </ThemedView>
  );
};

export default IncidentItem;
