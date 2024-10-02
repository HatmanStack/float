import { BackendMeditationCall } from "@/components/BackendMeditationCall";
import { Platform } from "react-native";

const mockBase64 = 'UklGRgAAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQAC/AAAAABAAEAQAAABAAAAAEAAAB9AAAA';

jest.mock("aws-sdk", () => ({
  Lambda: jest.fn(() => ({
    invoke: jest.fn((params, callback) => {
      const mockPayload = {
        Payload: JSON.stringify({ 
          body: JSON.stringify({ // <-- Add an extra layer of JSON stringification
            base64: mockBase64,
            music_list: ["music1", "music2"], 
          })
        })
      };
      
      callback(null,  mockPayload );// Simulate successful invocation
    }),
  })),
}));

// Mock FileSystem for non-web environments
jest.mock("expo-file-system", () => ({
  documentDirectory: "mock-directory/",
  writeAsStringAsync: jest.fn(() => Promise.resolve()),
  EncodingType: {
    Base64: 'base64', 
  },
}));

describe("BackendMeditationCall", () => {
  it("should successfully invoke Lambda function and return response", async () => {
    const selectedIndexes = [0, 1];
    
    const resolvedIncidents = [
      {
        sentiment_label: "Happy",
        intensity: "3",
        speech_to_text: "Some happy text",
        added_text: "More happy text",
        summary: "Summary of happy incident",
      },
      {
        sentiment_label: "Excited",
        intensity: "4",
        speech_to_text: "Some excited text",
        added_text: "More excited text",
        summary: "Summary of excitement",
      }
    ];
    const musicList = ["music1", "music2"];
    const user = "testuser";

    const webResponse = await BackendMeditationCall(
      selectedIndexes,
      resolvedIncidents,
      musicList,
      user
    );
    expect(webResponse).toEqual({
      responseMeditationURI: "mock-directory/output.mp3", 
      responseMusicList: ["music1", "music2"],
    });
   
  });
});
