//Possible Implementation
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { FlatList, Text } from "react-native";
import React, { useState, useEffect } from "react";
import ParallaxScrollView from "@/components/ParallaxScrollView";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import { useIncident } from "@/context/IncidentContext";
import useStyles from "@/constants/StylesConstants";
import { useWindowDimensions } from "react-native";

export default function ArchivedItemsScreen() {
  const [archivedItems, setArchivedItems] = useIncident();
  const { width, height } = useWindowDimensions();
  const styles = useStyles();

  useEffect(() => {
    // Fetch archived items from context or API
    const fetchArchivedItems = async () => {
      // Replace with actual fetch logic
      const items = await fetchArchivedItemsFromAPI();
      setArchivedItems(items);
    };

    fetchArchivedItems();
  }, []);

  const fetchArchivedItemsFromAPI = async () => {
    // Mock data, replace with actual API call
    return [
      { id: '1', title: 'Archived Item 1' },
      { id: '2', title: 'Archived Item 2' },
      { id: '3', title: 'Archived Item 3' },
    ];
  };

  const renderItem = ({ item }) => (
    <ThemedView style={styles.itemContainer}>
      <ThemedText>{item.title}</ThemedText>
    </ThemedView>
  );

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: "#bfaeba", dark: "#60465a" }}
      headerImage={
        <MaterialIcons
          size={310}
          name="history"
          style={styles.headerImage}
        />
      }
      headerText={<ThemedText type="header">fLoAt</ThemedText>}
    >
      <ThemedView style={styles.stepContainer}>
        <FlatList
          data={archivedItems}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
        />
      </ThemedView>
    </ParallaxScrollView>
  );
}