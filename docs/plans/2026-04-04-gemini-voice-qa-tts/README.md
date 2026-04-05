# Gemini Voice Q&A + TTS Migration

## Overview

This feature introduces two major changes to the Float meditation app. First, it migrates
the text-to-speech (TTS) provider from OpenAI (`gpt-4o-mini-tts`) to Gemini 2.5 Flash TTS
(`gemini-2.5-flash-preview-tts`), reducing cost by roughly 100x while keeping OpenAI as a
circuit-breaker fallback. The AI text generation model is also upgraded from Gemini 2.0 Flash
to 2.5 Flash for both sentiment analysis and meditation script generation.

Second, it adds a pre-meditation voice Q&A experience powered by the Gemini Live API. When a
user taps Generate, a short real-time voice conversation (2-3 exchanges) begins between the
user and a Gemini-powered agent. The agent uses the selected floats' sentiment data to ask
targeted questions, producing a transcript that enriches the meditation generation prompt.
The voice Q&A connects directly from the React Native client to the Gemini Live API via
WebSocket, with a short-lived token obtained from the Lambda backend to keep the API key
server-side. A text fallback is provided when microphone permission is denied.

## Prerequisites

- Node.js and npm (monorepo uses npm workspaces)
- Python 3.13 with pip (backend)
- Expo CLI (`npx expo`)
- Gemini API key with access to `gemini-2.5-flash-preview-tts` and Live API
- OpenAI API key (kept for fallback)
- AWS credentials for Lambda/S3 (deployment only)
- Install dependencies: `npm install --legacy-peer-deps`
- Backend deps: `cd backend && pip install -r requirements.txt`

## Phase Summary

| Phase | Goal | Token Estimate |
|-------|------|----------------|
| 0 | Foundation: architecture decisions, patterns, testing strategy | N/A (reference doc) |
| 1 | Backend TTS migration + model upgrade + token endpoint | ~40k |
| 2 | Frontend voice Q&A + backend transcript integration | ~45k |

## Navigation

- [Phase 0: Foundation](Phase-0.md)
- [Phase 1: Backend TTS Migration and Token Endpoint](Phase-1.md)
- [Phase 2: Frontend Voice Q&A and Transcript Integration](Phase-2.md)
- [Feedback Log](feedback.md)
- [Brainstorm](brainstorm.md)
