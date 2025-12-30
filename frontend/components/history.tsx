//Possible Implementation
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { FlatList } from 'react-native';
import React, { useEffect, useCallback } from 'react';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { useIncident } from '@/context/IncidentContext';
import useStyles from '@/constants/StylesConstants';

export default function ArchivedItemsScreen() {
  const { incidentList: archivedItems, setIncidentList: setArchivedItems } = useIncident();
  const styles = useStyles();

  interface ArchivedItem {
    id: string;
    title: string;
    timestamp?: string;
    sentiment_label?: string;
    intensity?: number | string;
  }

  const fetchArchivedItemsFromAPI = useCallback(async (): Promise<ArchivedItem[]> => {
    // Mock data, replace with actual API call
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
    // Fetch archived items from context or API
    const fetchArchivedItems = async () => {
      // Replace with actual fetch logic
      const items = await fetchArchivedItemsFromAPI();
      // Convert to Incident type format, normalizing intensity to number
      const incidents = items.map((item) => ({
        ...item,
        timestamp: item.timestamp || new Date().toISOString(),
        sentiment_label: item.sentiment_label || 'neutral',
        intensity: typeof item.intensity === 'string'
          ? parseInt(item.intensity, 10) || 1
          : item.intensity || 1,
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
