import AWS from "aws-sdk";

export async function BackendSummaryCall(
  recordingURI: any,
  separateTextPrompt: string
) {
  const data = {
    inference_type: "summary",
    audio: recordingURI ? recordingURI : "NotAvailable",
    prompt:
      separateTextPrompt && separateTextPrompt.length > 0
        ? separateTextPrompt
        : "NotAvailable",
    input_data: "NotAvailable",
  };

  const serializedData = JSON.stringify(data);

  const awsId = "AKIAZF4BCYP6R3HIBGEQ";
  const awsSecret = "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";
  const awsRegion = "us-west-1";

  try {
    const response = await invokeLambdaFunction(
      serializedData,
      awsId,
      awsSecret,
      awsRegion
    );

    return response;
  } catch (error) {
    console.error("Error invoking Lambda function:", error);
    throw error;
  }
}

async function invokeLambdaFunction(
  serializedData: string,
  awsId: string,
  awsSecret: string,
  awsRegion: string
) {
  try {
    const lambda = new AWS.Lambda({
      accessKeyId: awsId,
      secretAccessKey: awsSecret,
      region: awsRegion,
    });

    const params = {
      FunctionName: "audio-er-final",
      InvocationType: "RequestResponse",
      Payload: serializedData,
    };

    const data = await new Promise((resolve, reject) => {
      lambda.invoke(params, (err, data) => {
        if (err) {
          console.error(`An error occurred: ${err}`);
          reject(err);
        } else {
          resolve(data);
        }
      });
    });

    const responsePayload = JSON.parse(JSON.parse(data.Payload).body);
    responsePayload.timestamp = new Date().toISOString();
    responsePayload.color_key = 0;

    return responsePayload;
  } catch (e) {
    console.error("Error handling lambda invocation:", e);
    // Handle the error as needed
  }
}
