import { Tabs } from "expo-router";
import React from "react";
import { IncidentColoring } from "@/frontend/components/IncidentColoring";
import { IncidentProvider } from "@/frontend/context/IncidentContext";
import { IncidentSave } from "@/frontend/components/LocalFileLoadAndSave";
import { TabBarIcon } from "@/frontend/components/navigation/TabBarIcon";
import { Colors } from "@/frontend/constants/Colors";
import { useColorScheme } from "@/frontend/hooks/useColorScheme";
import { useAuth } from "@/frontend/context/AuthContext";
import AuthScreen from "@/frontend/components/AuthScreen";
export default function TabLayout(): React.ReactNode {
  const colorScheme = useColorScheme();
  const { user } = useAuth();
  return (
    <IncidentProvider>
      {!user ? (
        <AuthScreen />
      ) : (
        <>
          <IncidentColoring />
          <IncidentSave />
          <Tabs
            screenOptions={{
              tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
              headerShown: false,
            }}
          >
            <Tabs.Screen
              name="index"
              options={{
                title: 'Create',
                tabBarIcon: ({ color }) => <TabBarIcon name={'settings-voice'} color={color} />,
              }}
            />
            <Tabs.Screen
              name="explore"
              options={{
                title: 'Meditate',
                tabBarIcon: ({ color }) => <TabBarIcon name={'self-improvement'} color={color} />,
              }}
            />
          </Tabs>
        </>
      )}
    </IncidentProvider>
  );
}
