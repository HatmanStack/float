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
    user_id: "1234567"
  };

  const serializedData = JSON.stringify(data);
  
  const awsId = process.env.EXPO_PUBLIC_AWS_ID;
  const awsSecret = process.env.EXPO_PUBLIC_AWS_SECRET;
  const awsRegion = process.env.EXPO_PUBLIC_AWS_REGION;
  
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
    
    const responsePayloadString = JSON.parse(data.Payload).body;
    console.log("TYPE OF:", typeof responsePayloadString);
    console.log(responsePayloadString);
    
    let responsePayload;
    try {
        // Directly parse the JSON string
        responsePayload = JSON.parse(responsePayloadString);
        console.log("TYPE OF responsePayload:", typeof responsePayload); // Should log "object"
    } catch (error) {
        console.error('Error parsing responsePayload:', error);
    }
    responsePayload.timestamp = new Date().toISOString();
    responsePayload.color_key = 0;

    return responsePayload;
  } catch (e) {
    console.error("Error handling lambda invocation:", e);
    // Handle the error as needed
  }
}
