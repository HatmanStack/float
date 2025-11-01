import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Animated, Pressable, ViewStyle } from 'react-native';
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
}: any) => {
  const timestamp = new Date(incident.timestamp).toLocaleString();
  const { colorChangeArrayOfArrays } = useIncident();
  const displayText = selectedIndexes.includes(index)
    ? incident.user_summary
    : `${incident.user_short_summary} - ${timestamp}`;
  const [isSwiping, setIsSwiping] = useState(false);
  const styles = useStyles();
  const colors = useMemo(() => {
    if (Array.isArray(colorChangeArrayOfArrays) && colorChangeArrayOfArrays[index]?.length >= 2) {
      return colorChangeArrayOfArrays[index];
    }
    return ['#fff', '#fff'];
  }, [colorChangeArrayOfArrays, index]);
  const colorAnim = useRef(new Animated.Value(0));
  const animValueRef = useRef<any>(null);
  const [staticBackgroundColor, setStaticBackgroundColor] = useState(colors[0] || '#fff');
  const colorChangeDuration = 500;

  useEffect(() => {
    // Create animated interpolation inside effect to avoid render-time interpolation
    animValueRef.current = colorAnim.current.interpolate({
      inputRange: colors.map((_: any, i: any) => i),
      outputRange: colors,
    });

    // Set static color for non-animated components
    setStaticBackgroundColor(colors[0] || '#fff');

    const forwardAnimations = colors.map((_: any, i: any) =>
      Animated.timing(colorAnim.current, {
        toValue: i,
        duration: colorChangeDuration,
        useNativeDriver: false,
      })
    );

    const reverseAnimations = colors.map((_: any, i: any) =>
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

    return () => {
      animationLoop.stop();
    };
  }, [colors, isSwiping, colorChangeDuration]);

  const onPressHandler = (index: any) => {
    handlePress(index)(); // Call the returned function
  };

  // Create animated style outside of JSX to avoid ref access during render
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const animatedViewStyle = useMemo((): (ViewStyle | Animated.WithAnimatedObject<ViewStyle>)[] => {
    // eslint-disable-next-line no-console
    const animValue = animValueRef.current;
    if (animValue) {
      return [{ width: '100%' as const }, { backgroundColor: animValue }];
    }
    return [{ width: '100%' as const }, { backgroundColor: '#fff' }];
  }, []);

  return (
    <ThemedView style={styles.incidentContainer}>
      <Animated.View style={animatedViewStyle}>
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
