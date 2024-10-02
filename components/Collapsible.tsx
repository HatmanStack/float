import Ionicons from "@expo/vector-icons/Ionicons";
import { PropsWithChildren, useState } from "react";
import { StyleSheet, TouchableOpacity, useColorScheme } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import { Colors } from "@/constants/Colors";

export function Collapsible({
  children,
  title,
  incidentColor,
  textType,
  isOpen,
  onToggle,
}: PropsWithChildren & { title: string }) {
  const theme = useColorScheme() ?? "light";

  return (
    <ThemedView style={{ backgroundColor: incidentColor }}>
      <TouchableOpacity
        style={styles.heading}
        onPress={onToggle}
        activeOpacity={0.8}
      >
        <Ionicons
          name={isOpen ? "chevron-down" : "chevron-forward-outline"}
          size={18}
          color={
            textType
              ? '#fffff2'
              : theme === "light"
              ? Colors.light.icon
              : Colors.dark.icon
          }
        />
        <ThemedText type={textType ? textType : "subtitle"}>{title}</ThemedText>
      </TouchableOpacity>
      {isOpen && (
        <ThemedView
          style={[styles.content, { backgroundColor: incidentColor }]}
        >
          {children}
        </ThemedView>
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  heading: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  content: {
    marginTop: 6,
    marginLeft: 24,
  },
});
