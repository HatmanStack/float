import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { FlatList } from 'react-native';
import React, { useEffect, useCallback } from 'react';
import ParallaxScrollView from "@/frontend/components/ParallaxScrollView';
import { ThemedText } from "@/frontend/components/ThemedText';
import { ThemedView } from "@/frontend/components/ThemedView';
import { useIncident } from "@/frontend/context/IncidentContext';
import useStyles from "@/frontend/constants/StylesConstants';
export default function ArchivedItemsScreen() {
  const { incidentList: archivedItems, setIncidentList: setArchivedItems } = useIncident();
  const styles = useStyles();
  interface ArchivedItem {
    id: string;
    title: string;
    timestamp?: string;
    sentiment_label?: string;
    intensity?: 1 | 2 | 3 | 4 | 5 | string | number;
  }
  const fetchArchivedItemsFromAPI = useCallback(async (): Promise<ArchivedItem[]> => {
    return [
      {
        id: '1',
        title: 'Archived Item 1',
        timestamp: new Date().toISOString(),
        sentiment_label: 'neutral',
        intensity: 1,
      },
      {
        id: '2',
        title: 'Archived Item 2',
        timestamp: new Date().toISOString(),
        sentiment_label: 'neutral',
        intensity: 1,
      },
      {
        id: '3',
        title: 'Archived Item 3',
        timestamp: new Date().toISOString(),
        sentiment_label: 'neutral',
        intensity: 1,
      },
    ];
  }, []);
  useEffect(() => {
    const fetchArchivedItems = async () => {
      const items = await fetchArchivedItemsFromAPI();
      const incidents = items.map((item) => ({
        ...item,
        timestamp: item.timestamp || new Date().toISOString(),
        sentiment_label: item.sentiment_label || 'neutral',
        intensity: item.intensity || 1,
      }));
      setArchivedItems(incidents);
    };
    fetchArchivedItems();
  }, [fetchArchivedItemsFromAPI, setArchivedItems]);
  const renderItem = ({ item }: { item: ArchivedItem }) => (
    <ThemedView style={styles.stepContainer}>
      <ThemedText>{item.title}</ThemedText>
    </ThemedView>
  );
  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#bfaeba', dark: '#60465a' }}
      headerImage={<MaterialIcons size={310} name="history" style={styles.headerImage} />}
      headerText={<ThemedText type="header">fLoAt</ThemedText>}
    >
      <ThemedView style={styles.stepContainer}>
        <FlatList
          data={archivedItems as unknown as ArchivedItem[]}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
        />
      </ThemedView>
    </ParallaxScrollView>
  );
}
