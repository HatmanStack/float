import React from 'react';
import { ActivityIndicator, Pressable } from 'react-native';
import { ThemedText } from '@/frontend/components/ThemedText';
import { Colors } from '@/frontend/constants/Colors';
import useStyles from '@/frontend/constants/StylesConstants';
interface SubmitButtonProps {
  submitActivity: boolean;
  handleSummaryCall: () => void;
}
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
        styles.button,
      ]}
    >
      {({ pressed }) => (
        <ThemedText type="generate">{pressed ? 'SUBMITTING!' : 'Submit Float'}</ThemedText>
      )}
    </Pressable>
  );
};
export default SubmitButton;
