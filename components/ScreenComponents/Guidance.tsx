import React, { useState } from "react";
import { ThemedText } from "@/components/ThemedText";
import { Collapsible } from "@/components/Collapsible"; // Assuming these are custom components

const Guidance = () => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleCollapsible = () => {
    setIsOpen((prevState) => !prevState);
  };

  return (
    <Collapsible
      title="Guidance"
      incidentColor={{ light: "#808080", dark: "#151718" }}
      isOpen={isOpen}
      onToggle={toggleCollapsible}
    >
      <ThemedText type="details">
        Tap on the text to view the incident details this selects the incident
      </ThemedText>
      <ThemedText type="details">
        You can select up to 3 incidents at a time
      </ThemedText>
      <ThemedText type="details">
        Tap on generate to create a personal meditation about the selected
        incidents
      </ThemedText>
      <ThemedText type="details">
        The color change indicates time passage since incident
      </ThemedText>
      <ThemedText type="details">
        The green incidents are ready to be dealt with
      </ThemedText>
      <ThemedText type="details">Swipe left to delete</ThemedText>
    </Collapsible>
  );
};

export default Guidance;
