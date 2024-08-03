import AWS from 'aws-sdk';

export async function BackendSummaryCall (recordingURI: any, separateTextPrompt: any){
    
    console.log('called')
    const data = {
        inference_type: "summary",
        audio: recordingURI ? 'NotAvailable' : recordingURI,
        prompt: separateTextPrompt ? 'NotAvailable' : separateTextPrompt,
        input_data: "NotAvailable",
    };
  
  const serializedData = JSON.stringify(data);
  const awsId = '';
  const awsSecret = '';
  const awsRegion = 'us-west-1';
  
  try {
    const lambda = new AWS.Lambda({
      accessKeyId: awsId,
      secretAccessKey: awsSecret,
      region: awsRegion,
    });
    
    const params = {
      FunctionName: 'audio-er-final',
      InvocationType: 'RequestResponse',
      Payload: serializedData,
    };
    lambda.invoke(params, (err, data) => {
      if (err) {
        console.error(`An error occurred: ${err}`);
      } else {
        const responsePayload = JSON.parse(data.Payload).body
        console.log('Response:', responsePayload);
        const responseDict = JSON.parse(responsePayload);
        responseDict.timestamp = new Date().toISOString();
        responseDict.color_key = 0;
        return responseDict;
      }
    });
  } catch (e) {
    console.error(`An error occurred: ${e}`);
  }
  return null;
}