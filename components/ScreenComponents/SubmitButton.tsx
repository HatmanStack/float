import React from 'react';
import { ActivityIndicator, Pressable } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { Colors } from '@/constants/Colors';
import useStyles from '@/constants/StylesConstants';

/**
 * Props for SubmitButton component
 */
interface SubmitButtonProps {
  submitActivity: boolean;
  handleSummaryCall: () => void;
}

/**
 * Submit button component with loading state
 */
const SubmitButton: React.FC<SubmitButtonProps> = ({
  submitActivity,
  handleSummaryCall,
}: SubmitButtonProps): React.ReactNode => {
  const styles = useStyles();

  return submitActivity ? (
    <ActivityIndicator size="large" color={Colors['activityIndicator']} />
  ) : (
    <Pressable
      onPress={() => handleSummaryCall()}
      style={({ pressed }) => [
        {
          backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'],
        },
        styles.button, // Use the styles returned by useStyles
      ]}
    >
      {({ pressed }) => (
        <ThemedText type="generate">{pressed ? 'SUBMITTING!' : 'Submit Float'}</ThemedText>
      )}
    </Pressable>
  );
};

export default SubmitButton;
