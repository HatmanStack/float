import React from 'react';
import { ActivityIndicator, Pressable, TextInput, View, StyleSheet } from 'react-native';
import { ThemedText } from '@/components/ThemedText'; // Adjust the import according to your actual component library
import { Colors } from '@/constants/Colors';
import styles from '@/constants/StylesConstants'; 



const SubmitButton = ({ summaryCall, handleSummaryCall }) => (
    summaryCall ? (
      <ActivityIndicator size="large" color={Colors["activityIndicator"]} />
    ) : (
      <Pressable
        onPress={handleSummaryCall}
        style={({ pressed }) => [
          { backgroundColor: pressed ? Colors["buttonPressed"] : Colors["buttonUnpressed"] },
          styles.button
        ]}
      >
        {({ pressed }) => (
          <ThemedText type="generate">
            {pressed ? "SUBMITTING!" : "Submit Incident"}
          </ThemedText>
        )}
      </Pressable>
    )
  );


  export default SubmitButton;