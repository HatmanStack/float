import { Tabs } from "expo-router";
import React from "react";
import { IncidentColoring } from "@/components/IncidentColoring";
import { IncidentProvider } from "@/context/IncidentContext";
import { IncidentSave } from "@/components/LocalFileLoadAndSave";
import { TabBarIcon } from "@/components/navigation/TabBarIcon";
import { Colors } from "@/constants/Colors";
import { useColorScheme } from "@/hooks/useColorScheme";
import { useAuth } from '@/context/AuthContext';
import AuthScreen from "@/components/AuthScreen";


export default function TabLayout() {
  const colorScheme = useColorScheme();
  const { user } = useAuth();

  return (
    <IncidentProvider>
      
      {!user ? (<AuthScreen />) :(
        <>
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
                name={"settings-voice"}
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
      </>)}
      
    </IncidentProvider>
  );
}
