#!/bin/bash

# Helper functions for deployment script

generate_samconfig_toml() {
    local stack_name="$1"
    local region="$2"
    local ffmpeg_layer="$3"
    local gkey="$4"
    local openai_key="$5"
    local xi_key="$6"
    local similarity="$7"
    local stability="$8"
    local style="$9"
    local voice_id="${10}"
    local output_file="${11:-samconfig.toml}"

    cat > "$output_file" <<EOF
version = 0.1

[default.global.parameters]
stack_name = "$stack_name"
region = "$region"

[default.build.parameters]
cached = true
parallel = true

[default.deploy.parameters]
capabilities = "CAPABILITY_IAM"
confirm_changeset = false
resolve_s3 = true
s3_prefix = "$stack_name"
region = "$region"
parameter_overrides = "FFmpegLayerArn=\"$ffmpeg_layer\" GKey=\"$gkey\" OpenAIKey=\"$openai_key\" XIKey=\"$xi_key\" SimilarityBoost=\"$similarity\" Stability=\"$stability\" VoiceStyle=\"$style\" VoiceId=\"$voice_id\""
EOF
}

generate_frontend_env() {
    local api_endpoint="$1"
    local audio_bucket="$2"
    local output_file="$3"

    cat > "$output_file" <<EOF
EXPO_PUBLIC_LAMBDA_FUNCTION_URL=$api_endpoint
EXPO_PUBLIC_S3_BUCKET=$audio_bucket
EOF
}

validate_api_key_format() {
    local key="$1"
    local service="$2"

    if [ -z "$key" ]; then
        if [ "$service" == "ElevenLabs" ]; then
            return 0 # Optional
        fi
        return 1
    fi
    return 0
}
