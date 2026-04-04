import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  TextInput,
  Pressable,
  ActivityIndicator,
  Animated,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Audio } from 'expo-av';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { Colors } from '@/constants/Colors';
import { ThemedText } from '@/components/ThemedText';
import useGeminiLiveAPI from '@/hooks/useGeminiLiveAPI';
import type { TransformedDict } from '@/components/BackendMeditationCall';
import type { QATranscript } from '@/types/api';

interface VoiceQAProps {
  sentimentData: TransformedDict;
  onComplete: (transcript: QATranscript) => void;
  onSkip: () => void;
  onError: (error: Error) => void;
}

/**
 * Inline voice Q&A component that replaces the Generate button during conversation.
 * Falls back to text input when microphone permission is denied.
 */
const VoiceQA: React.FC<VoiceQAProps> = ({ sentimentData, onComplete, onSkip, onError }) => {
  const [textMode, setTextMode] = useState(false);
  const [textInput, setTextInput] = useState('');
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const hasCalledComplete = useRef(false);

  const { state, transcript, startSession, sendTextMessage } = useGeminiLiveAPI({
    sentimentData,
    onTranscriptComplete: (t) => {
      if (!hasCalledComplete.current) {
        hasCalledComplete.current = true;
        onComplete(t);
      }
    },
    onError,
  });

  // Request mic permission and start session on mount
  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        const { granted } = await Audio.requestPermissionsAsync();
        if (mounted) {
          setTextMode(!granted);
        }
        await startSession();
      } catch (error) {
        if (mounted) {
          onError(error instanceof Error ? error : new Error(String(error)));
        }
      }
    };

    init();

    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Pulsing animation for listening state
  useEffect(() => {
    if (state === 'listening' && !textMode) {
      const animation = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 0.4,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      );
      animation.start();
      return () => animation.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [state, textMode, pulseAnim]);

  // Call onComplete when state becomes complete
  useEffect(() => {
    if (state === 'complete' && !hasCalledComplete.current) {
      hasCalledComplete.current = true;
      onComplete(transcript);
    }
  }, [state, transcript, onComplete]);

  const handleSendText = useCallback(() => {
    if (textInput.trim()) {
      sendTextMessage(textInput.trim());
      setTextInput('');
    }
  }, [textInput, sendTextMessage]);

  const renderTranscript = () => {
    if (transcript.length === 0) return null;
    return (
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
    );
  };

  const renderStateIndicator = () => {
    switch (state) {
      case 'connecting':
        return (
          <View style={localStyles.stateRow}>
            <ActivityIndicator size="small" color={Colors['activityIndicator']} />
            <ThemedText style={localStyles.stateText}>Connecting...</ThemedText>
          </View>
        );
      case 'listening':
        if (textMode) {
          return (
            <View style={localStyles.stateRow}>
              <MaterialIcons name="keyboard" size={24} color={Colors['buttonPressed']} />
              <ThemedText style={localStyles.stateText}>Listening...</ThemedText>
            </View>
          );
        }
        return (
          <Animated.View style={[localStyles.stateRow, { opacity: pulseAnim }]}>
            <MaterialIcons name="mic" size={28} color={Colors['buttonPressed']} />
            <ThemedText style={localStyles.stateText}>Listening...</ThemedText>
          </Animated.View>
        );
      case 'processing':
        return (
          <View style={localStyles.stateRow}>
            <ActivityIndicator size="small" color={Colors['activityIndicator']} />
            <ThemedText style={localStyles.stateText}>Thinking...</ThemedText>
          </View>
        );
      case 'responding':
        return (
          <View style={localStyles.stateRow}>
            <MaterialIcons name="volume-up" size={24} color={Colors['buttonPressed']} />
            <ThemedText style={localStyles.stateText}>Speaking...</ThemedText>
          </View>
        );
      case 'complete':
        return (
          <View style={localStyles.stateRow}>
            <ThemedText style={localStyles.stateText}>Starting meditation...</ThemedText>
          </View>
        );
      default:
        return null;
    }
  };

  return (
    <View style={localStyles.container}>
      {textMode && (
        <ThemedText style={localStyles.textModeMessage}>
          Microphone not available. You can type your responses instead.
        </ThemedText>
      )}

      {renderTranscript()}
      {renderStateIndicator()}

      {textMode && state === 'listening' && (
        <View style={localStyles.textInputRow}>
          <TextInput
            style={localStyles.textInput}
            value={textInput}
            onChangeText={setTextInput}
            placeholder="Type your response..."
            placeholderTextColor="#999"
            returnKeyType="send"
            onSubmitEditing={handleSendText}
          />
          <Pressable
            onPress={handleSendText}
            style={({ pressed }) => [
              localStyles.sendButton,
              { backgroundColor: pressed ? Colors['buttonPressed'] : Colors['buttonUnpressed'] },
            ]}
          >
            <ThemedText style={localStyles.sendButtonText}>Send</ThemedText>
          </Pressable>
        </View>
      )}

      <Pressable
        onPress={() => {
          onSkip();
        }}
        style={localStyles.skipButton}
        testID="skip-qa-button"
      >
        <ThemedText style={localStyles.skipText}>Skip</ThemedText>
      </Pressable>
    </View>
  );
};

const localStyles = StyleSheet.create({
  container: {
    padding: 16,
    alignItems: 'center',
  },
  textModeMessage: {
    fontSize: 13,
    opacity: 0.7,
    textAlign: 'center',
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
  stateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginVertical: 12,
  },
  stateText: {
    fontSize: 15,
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
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  sendButtonText: {
    fontSize: 14,
    fontWeight: '600',
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
