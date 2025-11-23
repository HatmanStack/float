import os
import subprocess

# Path to the bash script wrapper for testing
# We are running pytest from backend/ directory, so path should be relative to that
DEPLOY_HELPERS_SCRIPT = "scripts/deploy-helpers.sh"


def run_bash_function(function_name, *args):
    """
    Helper to run a bash function from the source file.
    It constructs a small script that sources the helper file and calls the function.
    """
    args_str = " ".join([f"'{arg}'" for arg in args])
    cmd = f"source {DEPLOY_HELPERS_SCRIPT}; {function_name} {args_str}"

    # Run in bash
    result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
    return result


class TestDeployHelpers:
    def test_generate_samconfig_toml(self, tmp_path):
        output_file = tmp_path / "samconfig.toml"

        args = [
            "test-stack",  # stack_name
            "us-east-1",  # region
            "arn:aws:layer:1",  # ffmpeg_layer
            "gemini-key",  # gkey
            "openai-key",  # openai_key
            "xi-key",  # xi_key
            "0.8",  # similarity
            "0.4",  # stability
            "0.5",  # style
            "voice-123",  # voice_id
            str(output_file),  # output_file
        ]

        result = run_bash_function("generate_samconfig_toml", *args)
        assert result.returncode == 0

        assert output_file.exists()
        content = output_file.read_text()

        # Verify content structure
        assert 'stack_name = "test-stack"' in content
        assert 'region = "us-east-1"' in content
        assert 'parameter_overrides = "FFmpegLayerArn=\\"arn:aws:layer:1\\"' in content
        assert 'GKey=\\"gemini-key\\"' in content

    def test_generate_frontend_env(self, tmp_path):
        output_file = tmp_path / ".env"

        api_endpoint = "https://api.example.com"
        audio_bucket = "test-bucket"

        result = run_bash_function(
            "generate_frontend_env", api_endpoint, audio_bucket, str(output_file)
        )
        assert result.returncode == 0

        assert output_file.exists()
        content = output_file.read_text()

        assert f"EXPO_PUBLIC_LAMBDA_FUNCTION_URL={api_endpoint}" in content
        assert f"EXPO_PUBLIC_S3_BUCKET={audio_bucket}" in content

    def test_validate_api_key_format_valid(self):
        result = run_bash_function("validate_api_key_format", "some-key", "Service")
        assert result.returncode == 0

    def test_validate_api_key_format_invalid_empty(self):
        result = run_bash_function("validate_api_key_format", "", "Service")
        assert result.returncode == 1

    def test_validate_api_key_format_optional(self):
        # ElevenLabs key is optional
        result = run_bash_function("validate_api_key_format", "", "ElevenLabs")
        assert result.returncode == 0

    def test_gitignore_secrets(self, tmp_path):
        """Verify that samconfig.toml is ignored by git."""
        # Create dummy samconfig.toml in backend dir (current working dir)
        samconfig = "samconfig.toml"

        # Ensure file exists
        with open(samconfig, "w") as f:
            f.write("secret=true")

        try:
            # Check if ignored
            result = subprocess.run(
                ["git", "check-ignore", "-v", "samconfig.toml"],
                capture_output=True,
                text=True,
            )
            # Exit code 0 means ignored, 1 means not ignored
            assert result.returncode == 0
            assert ".gitignore" in result.stdout
        finally:
            # Cleanup
            if os.path.exists(samconfig):
                os.remove(samconfig)
