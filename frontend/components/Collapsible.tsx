import Ionicons from '@expo/vector-icons/Ionicons';
import React, { PropsWithChildren, useMemo } from 'react';
import { Animated, StyleSheet, TouchableOpacity, useColorScheme } from 'react-native';

import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { Colors } from '@/constants/Colors';

/**
 * Props for Collapsible component
 */
interface CollapsibleProps extends PropsWithChildren {
  title: string;
  incidentColor?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  animatedColor?: Animated.AnimatedInterpolation<any>;
  textType?: 'subtitle' | 'incidentSubtitle';
  isOpen: boolean;
  onToggle: () => void;
}

/**
 * Custom hook for collapsible icon color logic
 */
function useCollapsibleIconColor(textType: string | undefined, theme: 'light' | 'dark'): string {
  return useMemo(() => {
    if (textType) return '#fffff2';
    return theme === 'light' ? Colors.light.icon : Colors.dark.icon;
  }, [textType, theme]);
}

/**
 * Collapsible component with expandable content area
 */
export function Collapsible({
  children,
  title,
  incidentColor,
  animatedColor,
  textType,
  isOpen,
  onToggle,
}: CollapsibleProps): React.ReactNode {
  const theme = useColorScheme() ?? 'light';
  const iconColor = useCollapsibleIconColor(textType, theme);

  // Use animated view if animatedColor is provided
  if (animatedColor) {
    return (
      <Animated.View style={{ backgroundColor: animatedColor }}>
        <TouchableOpacity style={styles.heading} onPress={onToggle} activeOpacity={0.8}>
          <Ionicons
            name={isOpen ? 'chevron-down' : 'chevron-forward-outline'}
            size={18}
            color={iconColor}
          />
          <ThemedText type={textType ? textType : 'subtitle'}>{title}</ThemedText>
        </TouchableOpacity>
        {isOpen && (
          <Animated.View style={[styles.content, { backgroundColor: animatedColor }]}>
            {children}
          </Animated.View>
        )}
      </Animated.View>
    );
  }

  return (
    <ThemedView style={{ backgroundColor: incidentColor }}>
      <TouchableOpacity style={styles.heading} onPress={onToggle} activeOpacity={0.8}>
        <Ionicons
          name={isOpen ? 'chevron-down' : 'chevron-forward-outline'}
          size={18}
          color={iconColor}
        />
        <ThemedText type={textType ? textType : 'subtitle'}>{title}</ThemedText>
      </TouchableOpacity>
      {isOpen && (
        <ThemedView style={[styles.content, { backgroundColor: incidentColor }]}>
          {children}
        </ThemedView>
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  heading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  content: {
    marginTop: 6,
    marginLeft: 24,
  },
});
