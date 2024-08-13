import React from "react";
import { ActivityIndicator, Pressable } from "react-native";
import { ThemedText } from "@/components/ThemedText"; // Adjust the import according to your actual component library
import { Colors } from "@/constants/Colors";
import useStyles from "@/constants/StylesConstants"; // Ensure correct import

const SubmitButton = ({ submitActivity, handleSummaryCall }) => {
  const styles = useStyles(); // Call useStyles inside the component

  return submitActivity ? (
    <ActivityIndicator size="large" color={Colors["activityIndicator"]} />
  ) : (
    <Pressable
      onPress={() => handleSummaryCall()}
      style={({ pressed }) => [
        {
          backgroundColor: pressed
            ? Colors["buttonPressed"]
            : Colors["buttonUnpressed"],
        },
        styles.button, // Use the styles returned by useStyles
      ]}
    >
      {({ pressed }) => (
        <ThemedText type="generate">
          {pressed ? "SUBMITTING!" : "Submit Incident"}
        </ThemedText>
      )}
    </Pressable>
  );
};

export default SubmitButton;
