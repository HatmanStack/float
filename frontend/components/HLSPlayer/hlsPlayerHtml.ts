/**
 * HLS Player HTML template for WebView embedding
 * This HTML is loaded into a WebView on mobile platforms to provide HLS playback
 * using the HLS.js library from CDN.
 */

export const hlsPlayerHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HLS Player</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      background: transparent;
      overflow: hidden;
    }
    audio {
      display: none;
    }
  </style>
</head>
<body>
  <audio id="audio" playsinline></audio>

  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.0/dist/hls.min.js"></script>
  <script>
    (function() {
      'use strict';

      const audio = document.getElementById('audio');
      let hls = null;
      let currentUrl = null;

      // Send message to React Native
      function sendMessage(type, data = {}) {
        if (window.ReactNativeWebView) {
          window.ReactNativeWebView.postMessage(JSON.stringify({ type, ...data }));
        }
      }

      // Send ready message when script loads
      sendMessage('ready');

      // Audio event listeners
      audio.addEventListener('play', () => {
        sendMessage('playing');
      });

      audio.addEventListener('pause', () => {
        sendMessage('paused');
      });

      audio.addEventListener('ended', () => {
        sendMessage('complete');
      });

      audio.addEventListener('timeupdate', () => {
        sendMessage('timeupdate', {
          currentTime: audio.currentTime,
          duration: isFinite(audio.duration) ? audio.duration : null
        });
      });

      audio.addEventListener('loadedmetadata', () => {
        sendMessage('durationchange', {
          duration: isFinite(audio.duration) ? audio.duration : null
        });
      });

      audio.addEventListener('waiting', () => {
        sendMessage('buffering', { buffering: true });
      });

      audio.addEventListener('canplay', () => {
        sendMessage('buffering', { buffering: false });
      });

      audio.addEventListener('error', (e) => {
        const error = audio.error;
        sendMessage('error', {
          message: error ? error.message : 'Audio playback error',
          code: error ? error.code : -1
        });
      });

      // Check for native HLS support (Safari)
      function supportsNativeHLS() {
        return audio.canPlayType('application/vnd.apple.mpegurl') !== '';
      }

      // Initialize HLS playback
      function loadSource(url) {
        if (currentUrl === url) return;
        currentUrl = url;

        // Cleanup existing HLS instance
        if (hls) {
          hls.destroy();
          hls = null;
        }

        if (!url) {
          audio.src = '';
          return;
        }

        sendMessage('loading');

        if (supportsNativeHLS()) {
          // Use native HLS (Safari/iOS)
          audio.src = url;
          audio.load();
        } else if (Hls.isSupported()) {
          // Use HLS.js
          hls = new Hls({
            liveSyncDuration: 3,
            liveMaxLatencyDuration: 10,
            liveDurationInfinity: true,
            lowLatencyMode: true,
            manifestLoadingMaxRetry: 4,
            manifestLoadingRetryDelay: 1000,
            levelLoadingMaxRetry: 4,
            levelLoadingRetryDelay: 1000,
            fragLoadingMaxRetry: 6,
            fragLoadingRetryDelay: 1000
          });

          hls.on(Hls.Events.MANIFEST_PARSED, () => {
            sendMessage('loaded');
          });

          hls.on(Hls.Events.LEVEL_LOADED, (event, data) => {
            if (data.details.totalduration) {
              sendMessage('durationchange', {
                duration: data.details.totalduration
              });
            }
            // Detect stream completion
            if (data.details.live === false) {
              sendMessage('streamComplete');
            }
          });

          hls.on(Hls.Events.ERROR, (event, data) => {
            console.error('HLS Error:', data);
            if (data.fatal) {
              switch (data.type) {
                case Hls.ErrorTypes.NETWORK_ERROR:
                  hls.startLoad();
                  break;
                case Hls.ErrorTypes.MEDIA_ERROR:
                  hls.recoverMediaError();
                  break;
                default:
                  sendMessage('error', {
                    message: 'HLS fatal error: ' + data.details,
                    fatal: true
                  });
                  break;
              }
            }
          });

          hls.loadSource(url);
          hls.attachMedia(audio);
        } else {
          sendMessage('error', {
            message: 'HLS is not supported in this browser',
            fatal: true
          });
        }
      }

      // Handle commands from React Native
      function handleCommand(command, data) {
        switch (command) {
          case 'load':
            loadSource(data.url);
            break;
          case 'play':
            audio.play().catch(err => {
              sendMessage('error', { message: err.message });
            });
            break;
          case 'pause':
            audio.pause();
            break;
          case 'seek':
            if (isFinite(data.time)) {
              audio.currentTime = data.time;
            }
            break;
          case 'setVolume':
            audio.volume = Math.max(0, Math.min(1, data.volume || 1));
            break;
          default:
            console.warn('Unknown command:', command);
        }
      }

      // Listen for messages from React Native
      // React Native WebView sends messages via different mechanisms depending on platform
      document.addEventListener('message', (event) => {
        try {
          const msg = JSON.parse(event.data);
          handleCommand(msg.command, msg);
        } catch (e) {
          console.error('Error parsing message:', e);
        }
      });

      // Also handle messages via window
      window.addEventListener('message', (event) => {
        try {
          const msg = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
          handleCommand(msg.command, msg);
        } catch (e) {
          console.error('Error parsing message:', e);
        }
      });
    })();
  </script>
</body>
</html>`;
