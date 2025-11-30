import Ionicons from '@expo/vector-icons/Ionicons';
import React, { PropsWithChildren, useMemo } from 'react';
import { StyleSheet, TouchableOpacity, useColorScheme } from 'react-native';

import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { Colors } from '@/constants/Colors';

/**
 * Props for Collapsible component
 */
interface CollapsibleProps extends PropsWithChildren {
  title: string;
  incidentColor?: string;
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
  textType,
  isOpen,
  onToggle,
}: CollapsibleProps): React.ReactNode {
  const theme = useColorScheme() ?? 'light';
  const iconColor = useCollapsibleIconColor(textType, theme);

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
