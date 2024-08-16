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
        Tap on the text to view the float details this selects the float
      </ThemedText>
      <ThemedText type="details">
        You can select up to 3 floats at a time
      </ThemedText>
      <ThemedText type="details">
        Tap on generate to create a personal meditation about the selected
        float
      </ThemedText>
      <ThemedText type="details">
        The color change indicates time passage since the float was created
      </ThemedText>
      <ThemedText type="details">
        The green floats are ready to be dealt with
      </ThemedText>
      <ThemedText type="details">Swipe left to delete</ThemedText>
    </Collapsible>
  );
};

export default Guidance;
