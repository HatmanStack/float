import { Tabs } from 'expo-router';
import React from 'react';
import { IncidentColoring } from '@/components/IncidentColoring';
import { IncidentProvider } from '@/context/IncidentContext';
import { IncidentSave } from '@/components/LocalFileLoadAndSave';
import { TabBarIcon } from '@/components/navigation/TabBarIcon';
import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <IncidentProvider>
    <IncidentColoring />
    <IncidentSave />
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
        headerShown: false,
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, focused }) => (
            <TabBarIcon name={focused ? 'head-plus' : 'head-plus-outline'} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Discovery',
          tabBarIcon: ({ color, focused }) => (
            <TabBarIcon name={focused ? 'view-list' : 'view-list-outline'} color={color} />
          ),
        }}
      />
    </Tabs>
    </IncidentProvider>
  );
}