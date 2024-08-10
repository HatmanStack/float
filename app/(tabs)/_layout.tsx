import { Tabs } from "expo-router";
import React from "react";
import { IncidentColoring } from "@/components/IncidentColoring";
import { IncidentProvider } from "@/context/IncidentContext";
import { IncidentSave } from "@/components/LocalFileLoadAndSave";
import { TabBarIcon } from "@/components/navigation/TabBarIcon";
import { Colors } from "@/constants/Colors";
import { useColorScheme } from "@/hooks/useColorScheme";

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <IncidentProvider>
      <IncidentColoring />
      <IncidentSave />
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: Colors[colorScheme ?? "light"].tint,
          headerShown: false,
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Create",
            tabBarIcon: ({ color}) => (
              <TabBarIcon
                name={"create"}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="explore"
          options={{
            title: "Meditate",
            tabBarIcon: ({ color}) => (
              <TabBarIcon
                name={"self-improvement"}
                color={color}
              />
            ),
          }}
        />
      </Tabs>
    </IncidentProvider>
  );
}
