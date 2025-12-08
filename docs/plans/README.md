# HLS Streaming Implementation Plan

## Feature Overview

This plan implements HLS (HTTP Live Streaming) for meditation audio playback, reducing perceived wait time from ~2 minutes to ~4 seconds. Instead of generating a complete audio file before playback can begin, the system will generate 5-second audio segments progressively, allowing playback to start after the first segment is ready.

The implementation uses HLS.js as the unified player across all platforms (web native, WebView on mobile), with a live playlist that grows as segments are generated. Users can optionally download the complete MP3 after streaming finishes. The system includes fault tolerance through idempotent regeneration - if generation fails mid-stream, the cached TTS audio allows FFmpeg to retry without re-running expensive API calls.

Key architectural changes: FFmpeg outputs HLS segments instead of a single MP3, segments upload to S3 progressively with pre-signed URLs, the frontend uses HLS.js for playback, and a server-side concatenation step produces the downloadable MP3.

## Prerequisites

### Tools Required
- Node.js v24 LTS (via nvm)
- Python 3.13 (via uv)
- AWS CLI v2 configured with appropriate credentials
- SAM CLI for Lambda deployment
- FFmpeg v6.1+ (Lambda layer handles this)

### Environment Setup
- AWS account with S3, Lambda, API Gateway permissions
- Gemini API key (`G_KEY`)
- OpenAI API key (`OPENAI_API_KEY`)
- Existing Float deployment or fresh deploy capability

### Dependencies to Add
- **Frontend**: `hls.js` (web HLS playback)
- **Frontend**: `react-native-webview` (mobile HLS via WebView)
- **Backend**: No new Python dependencies (uses existing boto3, FFmpeg)

## Phase Summary

| Phase | Goal | Estimated Tokens |
|-------|------|------------------|
| 0 | Foundation - Architecture decisions, testing strategy, deployment specs | Reference document |
| 1 | Backend HLS Generation - FFmpeg HLS output, segment upload, playlist management, MP3 concatenation | ~85,000 |
| 2 | Frontend HLS Playback - HLS.js integration, WebView player, download option, error handling | ~70,000 |

## Navigation

- [Phase 0: Foundation](./Phase-0.md) - Architecture decisions and patterns (reference for all phases)
- [Phase 1: Backend HLS Generation](./Phase-1.md) - Server-side streaming infrastructure
- [Phase 2: Frontend HLS Playback](./Phase-2.md) - Client-side player and UI
