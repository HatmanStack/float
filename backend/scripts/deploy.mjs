import fs from 'fs';
import path from 'path';
import readline from 'readline';
import { spawn, execSync, execFileSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DEPLOY_CONFIG_PATH = path.join(__dirname, '..', '.deploy-config.json');
const ENV_DEPLOY_PATH = path.join(__dirname, '..', '.env.deploy');
const SAM_CONFIG_PATH = path.join(__dirname, '..', 'samconfig.toml');
const FRONTEND_ENV_PATH = path.join(__dirname, '..', '..', 'frontend', '.env');

export function createInterface() {
  return readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
}

export function question(rl, query) {
  return new Promise(resolve => rl.question(query, resolve));
}

async function checkPrerequisites() {
  console.log('Checking prerequisites...');
  try {
    execSync('aws sts get-caller-identity', { stdio: 'ignore' });
  } catch (e) {
    console.error('Error: AWS CLI not configured or missing credentials. Run "aws configure".');
    process.exit(1);
  }

  try {
    execSync('sam --version', { stdio: 'ignore' });
  } catch (e) {
    console.error('Error: SAM CLI not installed.');
    process.exit(1);
  }
}

function loadEnvDeploy() {
  const secrets = {};
  if (fs.existsSync(ENV_DEPLOY_PATH)) {
    const content = fs.readFileSync(ENV_DEPLOY_PATH, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIndex = trimmed.indexOf('=');
      if (eqIndex > 0) {
        const key = trimmed.slice(0, eqIndex).trim();
        const value = trimmed.slice(eqIndex + 1).trim();
        secrets[key] = value;
      }
    }
  }
  return secrets;
}

function saveEnvDeploy(secrets) {
  const lines = [
    '# Float Backend Secrets',
    '# This file is gitignored - do not commit',
    '',
    `G_KEY=${secrets.geminiApiKey || ''}`,
    `OPENAI_API_KEY=${secrets.openaiApiKey || ''}`,
    ''
  ];
  fs.writeFileSync(ENV_DEPLOY_PATH, lines.join('\n'));
}

export async function loadOrPromptConfig(rl) {
  let saved = {};
  if (fs.existsSync(DEPLOY_CONFIG_PATH)) {
    try {
      saved = JSON.parse(fs.readFileSync(DEPLOY_CONFIG_PATH, 'utf8'));
      console.log('Loaded previous configuration from .deploy-config.json\n');
    } catch (e) {
      console.warn('Failed to parse .deploy-config.json, using defaults.');
    }
  }

  // Load secrets from .env.deploy
  const secrets = loadEnvDeploy();

  // Get AWS account ID for unique bucket naming
  let accountId = '';
  try {
    accountId = execSync('aws sts get-caller-identity --query Account --output text', { encoding: 'utf8' }).trim();
  } catch (e) {
    accountId = Date.now().toString();
  }

  const defaults = {
    region: 'us-east-1',
    stackName: 'float-backend',
    environment: 'production',
    s3DataBucket: `float-data-${accountId}`,
    s3AudioBucket: `float-audio-${accountId}`,
    includeDevOrigins: 'false',
    productionOrigins: ''
  };

  // Merge saved config as new defaults
  const currentDefaults = { ...defaults, ...saved };

  const config = {};

  // Region
  const regionInput = await question(rl, `AWS Region [${currentDefaults.region}]: `);
  config.region = regionInput.trim() || currentDefaults.region;

  // Stack name
  const stackInput = await question(rl, `Stack Name [${currentDefaults.stackName}]: `);
  config.stackName = stackInput.trim() || currentDefaults.stackName;

  // Environment
  const envInput = await question(rl, `Environment (staging/production) [${currentDefaults.environment}]: `);
  const envVal = envInput.trim().toLowerCase();
  config.environment = (envVal === 'staging' || envVal === 'production') ? envVal : currentDefaults.environment;

  // S3 Data Bucket
  const dataInput = await question(rl, `S3 Data Bucket [${currentDefaults.s3DataBucket}]: `);
  config.s3DataBucket = dataInput.trim() || currentDefaults.s3DataBucket;

  // S3 Audio Bucket
  const audioInput = await question(rl, `S3 Audio Bucket [${currentDefaults.s3AudioBucket}]: `);
  config.s3AudioBucket = audioInput.trim() || currentDefaults.s3AudioBucket;

  // Include Dev Origins
  const devOriginsInput = await question(rl, `Include dev origins (wildcard CORS) (true/false) [${currentDefaults.includeDevOrigins}]: `);
  const devOriginsVal = devOriginsInput.trim().toLowerCase();
  config.includeDevOrigins = devOriginsVal === '' ? currentDefaults.includeDevOrigins : (devOriginsVal === 'true' ? 'true' : 'false');

  // Production Origins
  const prodOriginsInput = await question(rl, `Production origins (comma-separated) [${currentDefaults.productionOrigins || 'none'}]: `);
  config.productionOrigins = prodOriginsInput.trim() || currentDefaults.productionOrigins;

  // API Keys from .env.deploy
  const geminiSaved = secrets.G_KEY || '';
  const geminiPrompt = geminiSaved ? `Gemini API Key [hidden]: ` : 'Gemini API Key: ';
  const geminiInput = await question(rl, geminiPrompt);
  config.geminiApiKey = geminiInput.trim() || geminiSaved;
  if (!config.geminiApiKey) {
    console.error('Error: Gemini API Key is required.');
    process.exit(1);
  }

  const openaiSaved = secrets.OPENAI_API_KEY || '';
  const openaiPrompt = openaiSaved ? `OpenAI API Key [hidden]: ` : 'OpenAI API Key: ';
  const openaiInput = await question(rl, openaiPrompt);
  config.openaiApiKey = openaiInput.trim() || openaiSaved;
  if (!config.openaiApiKey) {
    console.error('Error: OpenAI API Key is required.');
    process.exit(1);
  }

  // Save non-secret config to .deploy-config.json
  const configToSave = {
    region: config.region,
    stackName: config.stackName,
    environment: config.environment,
    s3DataBucket: config.s3DataBucket,
    s3AudioBucket: config.s3AudioBucket,
    includeDevOrigins: config.includeDevOrigins,
    productionOrigins: config.productionOrigins
  };
  fs.writeFileSync(DEPLOY_CONFIG_PATH, JSON.stringify(configToSave, null, 2));

  // Save secrets to .env.deploy
  saveEnvDeploy({ geminiApiKey: config.geminiApiKey, openaiApiKey: config.openaiApiKey });

  return config;
}

export function generateSamConfig(config, s3Bucket, ffmpegLayerArn) {
  const overrides = [
    `Environment=${config.environment}`,
    `GeminiApiKey=${config.geminiApiKey}`,
    `OpenAIApiKey=${config.openaiApiKey}`,
    `S3DataBucket=${config.s3DataBucket}`,
    `S3AudioBucket=${config.s3AudioBucket}`,
    `IncludeDevOrigins=${config.includeDevOrigins}`,
    `FfmpegLayerArn=${ffmpegLayerArn}`
  ];

  if (config.productionOrigins) {
    overrides.push(`ProductionOrigins="${config.productionOrigins}"`);
  }

  const parameterOverrides = overrides.join(' ');

  let content = `version = 0.1
[default.deploy.parameters]
stack_name = "${config.stackName}"
region = "${config.region}"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "${parameterOverrides}"
`;

  if (s3Bucket) {
    content += `s3_bucket = "${s3Bucket}"\n`;
  } else {
    content += `resolve_s3 = true\n`;
  }

  fs.writeFileSync(SAM_CONFIG_PATH, content);
  console.log('Generated samconfig.toml');
  return content;
}

function ensureFfmpegLayer(region, samBucket) {
  const layerName = 'ffmpeg';
  console.log(`Checking for ffmpeg Lambda layer in ${region}...`);

  try {
    // Check if layer already exists
    const result = execSync(
      `aws lambda list-layer-versions --layer-name ${layerName} --region ${region} --query "LayerVersions[0].LayerVersionArn" --output text`,
      { encoding: 'utf8' }
    ).trim();

    if (result && result !== 'None' && !result.includes('ResourceNotFoundException')) {
      console.log(`Found existing ffmpeg layer: ${result}`);
      return result;
    }
  } catch (e) {
    // Layer doesn't exist, continue to create it
  }

  console.log('Creating ffmpeg Lambda layer (this may take a minute)...');

  const tmpDir = path.join(__dirname, '..', '.ffmpeg-layer-tmp');
  const zipPath = path.join(tmpDir, 'ffmpeg-layer.zip');
  const s3Key = 'ffmpeg-layer.zip';

  try {
    // Create temp directory
    fs.mkdirSync(path.join(tmpDir, 'bin'), { recursive: true });

    // Download lightweight ffmpeg build (smaller than full static build)
    console.log('Downloading ffmpeg build for Lambda...');
    execSync(
      `curl -sL https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-linux-64.zip -o ffmpeg.zip && unzip -o ffmpeg.zip -d "${path.join(tmpDir, 'bin')}" && rm ffmpeg.zip`,
      { stdio: 'inherit', cwd: tmpDir }
    );
    // Make executable
    execSync(`chmod +x "${path.join(tmpDir, 'bin', 'ffmpeg')}"`, { stdio: 'pipe' });

    // Create zip
    console.log('Creating layer zip...');
    execSync(`zip -r "${zipPath}" bin`, { cwd: tmpDir, stdio: 'pipe' });

    // Upload to S3 (required for large layers >70MB)
    console.log(`Uploading layer to S3 (${samBucket})...`);
    execSync(`aws s3 cp "${zipPath}" s3://${samBucket}/${s3Key} --region ${region}`, { stdio: 'inherit' });

    // Publish layer from S3
    console.log('Publishing Lambda layer...');
    const publishResult = execSync(
      `aws lambda publish-layer-version --layer-name ${layerName} --content S3Bucket=${samBucket},S3Key=${s3Key} --compatible-runtimes python3.11 python3.12 python3.13 --compatible-architectures x86_64 --region ${region} --query "LayerVersionArn" --output text`,
      { encoding: 'utf8' }
    ).trim();

    // Cleanup S3
    execSync(`aws s3 rm s3://${samBucket}/${s3Key} --region ${region}`, { stdio: 'pipe' });

    console.log(`Created ffmpeg layer: ${publishResult}`);
    return publishResult;
  } finally {
    // Cleanup local
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

function ensureSamBucket(region) {
  console.log('Ensuring SAM managed S3 bucket exists...');
  try {
    // Check if bucket exists by listing SAM buckets in the region
    const result = execSync(`aws s3api list-buckets --query "Buckets[?starts_with(Name, 'aws-sam-cli-managed-default')].Name" --output text`, { encoding: 'utf8' });
    const buckets = result.trim().split(/\s+/).filter(b => b);

    // Check if any bucket is in our region
    for (const bucket of buckets) {
      try {
        const location = execSync(`aws s3api get-bucket-location --bucket ${bucket} --output text`, { encoding: 'utf8' }).trim();
        // us-east-1 returns 'None' or empty
        const bucketRegion = location === 'None' || location === '' ? 'us-east-1' : location;
        if (bucketRegion === region) {
          console.log(`Found SAM bucket: ${bucket}`);
          return bucket;
        }
      } catch (e) {
        // Bucket might not be accessible, continue
      }
    }

    // No bucket found, create one
    console.log(`Creating SAM managed bucket in ${region}...`);
    const bucketName = `aws-sam-cli-managed-default-${region}-${Date.now()}`;
    if (region === 'us-east-1') {
      execSync(`aws s3api create-bucket --bucket ${bucketName}`, { stdio: 'inherit' });
    } else {
      execSync(`aws s3api create-bucket --bucket ${bucketName} --region ${region} --create-bucket-configuration LocationConstraint=${region}`, { stdio: 'inherit' });
    }
    console.log(`Created SAM bucket: ${bucketName}`);
    return bucketName;
  } catch (e) {
    console.warn('Could not ensure SAM bucket, will let SAM handle it.');
    return null;
  }
}

async function buildAndDeploy() {
  console.log('Building SAM application...');
  try {
    execSync('sam build', { stdio: 'inherit', cwd: path.join(__dirname, '..') });
  } catch (e) {
    console.error('Build failed.');
    process.exit(1);
  }

  console.log('Deploying SAM application...');
  return new Promise((resolve, reject) => {
    const deploy = spawn('sam', ['deploy', '--no-confirm-changeset', '--no-fail-on-empty-changeset'], {
      cwd: path.join(__dirname, '..'),
      shell: true
    });

    let stdoutData = '';

    deploy.stdout.on('data', (data) => {
      const str = data.toString();
      process.stdout.write(str);
      stdoutData += str;
    });

    deploy.stderr.on('data', (data) => {
      process.stderr.write(data);
    });

    deploy.on('close', (code) => {
      if (code !== 0) {
        console.error(`Deployment failed with code ${code}`);
        reject(new Error('Deployment failed'));
      } else {
        resolve(stdoutData);
      }
    });
  });
}

async function getStackOutputs(stackName, region) {
  try {
    const result = execFileSync('aws', [
      'cloudformation',
      'describe-stacks',
      '--stack-name',
      stackName,
      '--region',
      region,
      '--query',
      'Stacks[0].Outputs',
      '--output',
      'json'
    ]);
    return JSON.parse(result.toString());
  } catch (e) {
    console.error('Failed to get stack outputs');
    return [];
  }
}

function updateFrontendEnv(apiUrl) {
  let envContent = '';
  if (fs.existsSync(FRONTEND_ENV_PATH)) {
    envContent = fs.readFileSync(FRONTEND_ENV_PATH, 'utf8');
  }

  const lines = envContent.split('\n');
  let foundApiUrl = false;
  let foundWebClientId = false;

  const newLines = lines.map(line => {
    if (line.startsWith('EXPO_PUBLIC_LAMBDA_FUNCTION_URL=')) {
      foundApiUrl = true;
      return `EXPO_PUBLIC_LAMBDA_FUNCTION_URL=${apiUrl}`;
    }
    if (line.startsWith('EXPO_PUBLIC_WEB_CLIENT_ID=')) {
      foundWebClientId = true;
    }
    return line;
  });

  if (!foundApiUrl) {
    newLines.push(`EXPO_PUBLIC_LAMBDA_FUNCTION_URL=${apiUrl}`);
  }

  // Add placeholder for Google Web Client ID if not present
  if (!foundWebClientId) {
    newLines.push('# Google OAuth Web Client ID (required for web Google Sign-in)');
    newLines.push('EXPO_PUBLIC_WEB_CLIENT_ID=placeholder');
  }

  const finalContent = newLines.filter(l => l.trim() !== '' || newLines.indexOf(l) === newLines.length - 1).join('\n');
  const tmpPath = FRONTEND_ENV_PATH + '.tmp';
  fs.writeFileSync(tmpPath, finalContent.endsWith('\n') ? finalContent : finalContent + '\n');
  fs.renameSync(tmpPath, FRONTEND_ENV_PATH);
  console.log(`Updated frontend .env with API URL: ${apiUrl}`);
}

async function main() {
  await checkPrerequisites();
  const rl = createInterface();
  const config = await loadOrPromptConfig(rl);
  rl.close();

  // Ensure SAM bucket exists first (needed for ffmpeg layer upload)
  const samBucket = ensureSamBucket(config.region);

  // Ensure ffmpeg layer exists (uses SAM bucket for upload)
  const ffmpegLayerArn = ensureFfmpegLayer(config.region, samBucket);

  generateSamConfig(config, samBucket, ffmpegLayerArn);

  try {
    await buildAndDeploy();
  } catch (e) {
    process.exit(1);
  }

  console.log('Deployment complete. Fetching outputs...');
  const outputs = await getStackOutputs(config.stackName, config.region);
  const apiUrlOutput = outputs.find(o => o.OutputKey === 'ApiUrl');

  if (apiUrlOutput) {
    updateFrontendEnv(apiUrlOutput.OutputValue);
  } else {
    console.warn('Could not find ApiUrl in stack outputs.');
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}
