import React, { useState, useCallback } from 'react';
import { View, TextInput, Pressable, StyleSheet, ScrollView } from 'react-native';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { Colors } from '@/constants/Colors';
import { ThemedText } from '@/components/ThemedText';
import type { TransformedDict } from '@/components/BackendMeditationCall';
import type { QATranscript, QAExchange } from '@/types/api';

const MAX_EXCHANGES = 3;

const CHECKIN_PROMPTS = [
  'How are you feeling right now, in this moment?',
  'Is there anything specific weighing on your mind?',
  "Thank you for sharing. Let me create a meditation tailored to what you've told me.",
];

interface VoiceQAProps {
  sentimentData: TransformedDict;
  userId?: string;
  onComplete: (transcript: QATranscript) => void;
  onSkip: () => void;
  onError: (error: Error) => void;
}

/**
 * Text-based Q&A check-in before meditation generation.
 * Collects user responses and passes them as transcript context
 * for a more personalized meditation. Voice proxy is on the roadmap.
 */
const VoiceQA: React.FC<VoiceQAProps> = ({ onComplete, onSkip }) => {
  const [textInput, setTextInput] = useState('');
  const [transcript, setTranscript] = useState<QAExchange[]>([
    { role: 'assistant', text: CHECKIN_PROMPTS[0] },
  ]);
  const [exchangeCount, setExchangeCount] = useState(0);

  const handleSendText = useCallback(() => {
    if (!textInput.trim()) return;

    const userExchange: QAExchange = { role: 'user', text: textInput.trim() };
    const nextCount = exchangeCount + 1;

    if (nextCount >= MAX_EXCHANGES) {
      // Final exchange — complete with full transcript
      const finalTranscript = [
        ...transcript,
        userExchange,
        { role: 'assistant' as const, text: CHECKIN_PROMPTS[CHECKIN_PROMPTS.length - 1] },
      ];
      setTranscript(finalTranscript);
      setTextInput('');
      onComplete(finalTranscript);
    } else {
      // Add user response and next prompt
      const nextPrompt = CHECKIN_PROMPTS[Math.min(nextCount, CHECKIN_PROMPTS.length - 1)];
      const updated = [
        ...transcript,
        userExchange,
        { role: 'assistant' as const, text: nextPrompt },
      ];
      setTranscript(updated);
      setExchangeCount(nextCount);
      setTextInput('');
    }
  }, [textInput, exchangeCount, transcript, onComplete]);

  return (
    <View style={localStyles.container}>
      <ThemedText style={localStyles.headerText}>Quick check-in</ThemedText>

      <ScrollView style={localStyles.transcriptContainer}>
        {transcript.map((exchange, index) => (
          <View
            key={index}
            style={[
              localStyles.exchangeRow,
              exchange.role === 'assistant' ? localStyles.assistantRow : localStyles.userRow,
            ]}
          >
            <ThemedText style={localStyles.roleLabel}>
              {exchange.role === 'assistant' ? 'Guide' : 'You'}
            </ThemedText>
            <ThemedText style={localStyles.exchangeText}>{exchange.text}</ThemedText>
          </View>
        ))}
      </ScrollView>

      <View style={localStyles.textInputRow}>
        <TextInput
          style={localStyles.textInput}
          value={textInput}
          onChangeText={setTextInput}
          placeholder="Type your response..."
          placeholderTextColor="#999"
          returnKeyType="send"
          onSubmitEditing={handleSendText}
          autoFocus
        />
        <Pressable
          onPress={handleSendText}
          style={({ pressed }) => [
            localStyles.sendButton,
            { backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'] },
          ]}
        >
          <MaterialIcons name="send" size={20} color="#fff" />
        </Pressable>
      </View>

      <Pressable onPress={onSkip} style={localStyles.skipButton} testID="skip-qa-button">
        <ThemedText style={localStyles.skipText}>Skip check-in</ThemedText>
      </Pressable>
    </View>
  );
};

const localStyles = StyleSheet.create({
  container: {
    padding: 16,
    alignItems: 'center',
  },
  headerText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  transcriptContainer: {
    maxHeight: 200,
    width: '100%',
    marginBottom: 12,
  },
  exchangeRow: {
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  assistantRow: {
    backgroundColor: Colors['buttonUnpressed'],
    alignSelf: 'flex-start',
    maxWidth: '85%',
  },
  userRow: {
    backgroundColor: Colors['buttonPressed'],
    alignSelf: 'flex-end',
    maxWidth: '85%',
  },
  roleLabel: {
    fontSize: 11,
    fontWeight: '700',
    opacity: 0.6,
    marginBottom: 2,
  },
  exchangeText: {
    fontSize: 14,
  },
  textInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginTop: 8,
    gap: 8,
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 14,
    color: '#333',
  },
  sendButton: {
    padding: 10,
    borderRadius: 8,
  },
  skipButton: {
    marginTop: 16,
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  skipText: {
    fontSize: 13,
    opacity: 0.6,
  },
});

export default VoiceQA;
