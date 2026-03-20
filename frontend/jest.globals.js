// Polyfill expo 55 globals for jest
// Must run before test framework loads modules

if (!globalThis.__ExpoImportMetaRegistry) {
  globalThis.__ExpoImportMetaRegistry = {
    register: () => {},
    get: () => ({}),
  };
}

if (typeof globalThis.structuredClone === 'undefined') {
  globalThis.structuredClone = (val) => JSON.parse(JSON.stringify(val));
}

// Use Node's built-in TextEncoder/TextDecoder when available (provides real
// encode/decode behavior). Fall back to stubs only if util module is missing.
// Expo's lazy global installer uses Object.defineProperty getters that call
// require() — in Jest 30 these fail outside test code scope.
try {
  const util = require('util');
  if (typeof globalThis.TextEncoder === 'undefined' && util.TextEncoder) {
    globalThis.TextEncoder = util.TextEncoder;
  }
  if (typeof globalThis.TextDecoder === 'undefined' && util.TextDecoder) {
    globalThis.TextDecoder = util.TextDecoder;
  }
} catch {
  // util not available — fall back to stubs
  if (typeof globalThis.TextEncoder === 'undefined') {
    globalThis.TextEncoder = class TextEncoder {
      encode(input = '') {
        return new Uint8Array([...input].map((c) => c.charCodeAt(0)));
      }
    };
  }
  if (typeof globalThis.TextDecoder === 'undefined') {
    globalThis.TextDecoder = class TextDecoder {
      decode() {
        return '';
      }
    };
  }
}

if (typeof globalThis.TextDecoderStream === 'undefined') {
  globalThis.TextDecoderStream = class TextDecoderStream {};
}
if (typeof globalThis.TextEncoderStream === 'undefined') {
  globalThis.TextEncoderStream = class TextEncoderStream {};
}
