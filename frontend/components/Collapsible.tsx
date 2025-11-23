import Ionicons from "@expo/vector-icons/Ionicons";
import React, { PropsWithChildren, useMemo } from "react";
import { StyleSheet, TouchableOpacity, useColorScheme } from "react-native";
import { ThemedText } from "@/frontend/components/ThemedText";
import { ThemedView } from "@/frontend/components/ThemedView";
import { Colors } from "@/frontend/constants/Colors";
interface CollapsibleProps extends PropsWithChildren {
  title: string;
  incidentColor?: string;
  textType?: 'subtitle' | 'incidentSubtitle';
  isOpen: boolean;
  onToggle: () => void;
}
function useCollapsibleIconColor(textType: string | undefined, theme: 'light' | 'dark'): string {
  return useMemo(() => {
    if (textType) return '#fffff2";
    return theme === 'light' ? Colors.light.icon : Colors.dark.icon;
  }, [textType, theme]);
}
export function Collapsible({
  children,
  title,
  incidentColor,
  textType,
  isOpen,
  onToggle,
}: CollapsibleProps): React.ReactNode {
  const theme = useColorScheme() ?? 'light";
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
