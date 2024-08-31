import { BackendMeditationCall } from "@/components/BackendMeditationCall";

// Mock AWS Lambda invoke function
jest.mock("aws-sdk", () => ({
  Lambda: jest.fn(() => ({
    invoke: jest.fn((params, callback) => {
      const mockPayload = {
        body: JSON.stringify({
          base64: "mocked-base64-data",
          music_list: ["music1", "music2"],
        }),
      };
      callback(null, { Payload: mockPayload });// Simulate successful invocation
    }),
  })),
}));

// Mock FileSystem for non-web environments
jest.mock("expo-file-system", () => ({
  documentDirectory: "mock-directory/",
  writeAsStringAsync: jest.fn(() => Promise.resolve()),
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

    const response = await BackendMeditationCall(
      selectedIndexes,
      resolvedIncidents,
      musicList,
      user
    );

    expect(response).toEqual({
      responseMeditationURI:
        typeof window !== "undefined"
          ? "blob:null/mocked-blob-url" // Adjust for web
          : "mock-directory/output.mp3", // Adjust for mobile
      responseMusicList: ["music1", "music2"],
    });
  });

  // Add more tests to cover error handling, different inputs, etc.
});
