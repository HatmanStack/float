import { useState, useRef, useCallback, useEffect } from 'react';
import type { TransformedDict } from '@/components/BackendMeditationCall';
import type { QAState, QAExchange, QATranscript } from '@/types/api';

const LAMBDA_FUNCTION_URL = process.env.EXPO_PUBLIC_LAMBDA_FUNCTION_URL || '';
const MAX_ASSISTANT_EXCHANGES = 3;

interface UseGeminiLiveAPIOptions {
  sentimentData: TransformedDict;
  onTranscriptComplete: (transcript: QATranscript) => void;
  onError: (error: Error) => void;
  userId?: string;
}

interface UseGeminiLiveAPIReturn {
  state: QAState;
  transcript: QAExchange[];
  startSession: () => Promise<void>;
  endSession: () => void;
  sendAudioChunk: (chunk: ArrayBuffer) => void;
  sendTextMessage: (text: string) => void;
}

function buildSystemPrompt(sentimentData: TransformedDict): string {
  const sentiments = sentimentData.sentiment_label.join(', ');
  const summaries = sentimentData.summary.join('; ');
  const intensities = sentimentData.intensity.join(', ');

  return (
    `You are a compassionate meditation guide doing a brief check-in before creating a ` +
    `personalized meditation. The user has shared some stressful moments.\n\n` +
    `Their emotional state: ${sentiments} (intensity: ${intensities})\n` +
    `Summary of their experiences: ${summaries}\n\n` +
    `Instructions:\n` +
    `- Ask 1-2 targeted questions about how the user is feeling right now\n` +
    `- Reference specific incidents from the data above\n` +
    `- Keep the conversation to 2-3 total exchanges\n` +
    `- Be warm, empathetic, and concise\n` +
    `- End by saying something like "Thank you for sharing. Let me create a meditation ` +
    `tailored to what you've told me."`
  );
}

/**
 * Custom hook for managing a Gemini Live API WebSocket session.
 * Handles token exchange, audio/text streaming, and transcript capture.
 */
export default function useGeminiLiveAPI(options: UseGeminiLiveAPIOptions): UseGeminiLiveAPIReturn {
  const { sentimentData, onTranscriptComplete, onError, userId } = options;

  const [state, setState] = useState<QAState>('idle');
  const [transcript, setTranscript] = useState<QAExchange[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const assistantExchangeCountRef = useRef(0);
  const transcriptRef = useRef<QAExchange[]>([]);

  // Keep transcriptRef in sync
  useEffect(() => {
    transcriptRef.current = transcript;
  }, [transcript]);

  const completeSession = useCallback(
    (finalTranscript?: QAExchange[]) => {
      setState('complete');
      wsRef.current?.close();
      onTranscriptComplete(finalTranscript ?? transcriptRef.current);
    },
    [onTranscriptComplete]
  );

  const startSession = useCallback(async () => {
    try {
      if (!LAMBDA_FUNCTION_URL) {
        throw new Error('Missing EXPO_PUBLIC_LAMBDA_FUNCTION_URL configuration');
      }

      setState('connecting');
      assistantExchangeCountRef.current = 0;
      setTranscript([]);

      // Fetch token from backend
      const baseUrl = LAMBDA_FUNCTION_URL.replace(/\/$/, '');
      const tokenResponse = await fetch(
        `${baseUrl}/token?user_id=${encodeURIComponent(userId || 'guest')}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!tokenResponse.ok) {
        throw new Error(`Token request failed with status ${tokenResponse.status}`);
      }

      const tokenData = await tokenResponse.json();
      const { token, endpoint: wsUrl } = tokenData;

      if (!wsUrl) {
        onError(new Error('No WebSocket endpoint returned'));
        setState('idle');
        return;
      }

      // Open WebSocket to Gemini Live API
      const wsEndpoint = `${wsUrl}?key=${token}`;
      const ws = new WebSocket(wsEndpoint);
      wsRef.current = ws;

      ws.onopen = () => {
        // Send setup message with system prompt
        const setupMessage = {
          setup: {
            model: 'models/gemini-2.5-flash-preview-native-audio-dialog',
            generationConfig: {
              responseModalities: ['TEXT'],
            },
            input_audio_transcription: {},
            systemInstruction: {
              parts: [{ text: buildSystemPrompt(sentimentData) }],
            },
          },
        };
        ws.send(JSON.stringify(setupMessage));
        setState('listening');
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;

          // Handle server content (model responses)
          if (data.serverContent) {
            const serverContent = data.serverContent;

            if (serverContent.modelTurn?.parts) {
              const textParts = serverContent.modelTurn.parts
                .filter((p: { text?: string }) => p.text)
                .map((p: { text: string }) => p.text);

              if (textParts.length > 0) {
                const assistantText = textParts.join('');
                setState('responding');

                if (serverContent.turnComplete) {
                  assistantExchangeCountRef.current += 1;
                  const exchange: QAExchange = { role: 'assistant', text: assistantText };
                  const updatedTranscript = [...transcriptRef.current, exchange];
                  setTranscript(updatedTranscript);

                  if (assistantExchangeCountRef.current >= MAX_ASSISTANT_EXCHANGES) {
                    completeSession(updatedTranscript);
                  } else {
                    setState('listening');
                  }
                }
              }
            } else if (serverContent.turnComplete) {
              setState('listening');
            }

            // Handle user speech transcription from voice input
            if (serverContent.inputTranscription) {
              const { text, finished } = serverContent.inputTranscription;
              if (finished && text) {
                const exchange: QAExchange = { role: 'user', text };
                setTranscript((prev) => [...prev, exchange]);
              }
            }
          }

          // Handle setup complete
          if (data.setupComplete) {
            setState('listening');
          }
        } catch {
          // Ignore parse errors for binary audio data
        }
      };

      ws.onerror = () => {
        onError(new Error('WebSocket connection error'));
        setState('idle');
      };

      ws.onclose = () => {
        // Only reset to idle if not already complete
        setState((prev) => (prev === 'complete' ? prev : 'idle'));
      };
    } catch (error) {
      onError(error instanceof Error ? error : new Error(String(error)));
      setState('idle');
    }
  }, [sentimentData, onError, completeSession, userId]);

  const endSession = useCallback(() => {
    wsRef.current?.close();
    setState('complete');
    onTranscriptComplete(transcriptRef.current);
  }, [onTranscriptComplete]);

  const sendAudioChunk = useCallback((chunk: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Encode in 32k slices to avoid RangeError from spread on large buffers
      const bytes = new Uint8Array(chunk);
      const SLICE_SIZE = 32768;
      let binary = '';
      for (let i = 0; i < bytes.length; i += SLICE_SIZE) {
        const slice = bytes.subarray(i, Math.min(i + SLICE_SIZE, bytes.length));
        binary += String.fromCharCode.apply(null, Array.from(slice));
      }
      const message = {
        realtimeInput: {
          mediaChunks: [
            {
              mimeType: 'audio/pcm;rate=16000',
              data: btoa(binary),
            },
          ],
        },
      };
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const sendTextMessage = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        clientContent: {
          turns: [{ role: 'user', parts: [{ text }] }],
          turnComplete: true,
        },
      };
      wsRef.current.send(JSON.stringify(message));

      // Add to transcript
      const exchange: QAExchange = { role: 'user', text };
      setTranscript((prev) => [...prev, exchange]);
      setState('processing');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return {
    state,
    transcript,
    startSession,
    endSession,
    sendAudioChunk,
    sendTextMessage,
  };
}
