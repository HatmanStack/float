# ADR-0008: Environment Variables for Secrets Management

**Status**: Accepted

**Date**: 2025-11-19

**Context**: The Float backend Lambda function requires sensitive credentials (Google Gemini API key, OpenAI API key, ElevenLabs API key, AWS S3 bucket names, AWS region). These secrets must be stored securely and made available to the Lambda function at runtime. AWS offers multiple options for secrets management: Lambda environment variables, AWS Secrets Manager, AWS Systems Manager Parameter Store, or external secret management services.

**Decision**: Store API keys and configuration as Lambda environment variables, configured via SAM template parameters, not AWS Secrets Manager or SSM Parameter Store.

**Alternatives Considered**:

1. **AWS Secrets Manager**
   - Pros: Automatic rotation, versioning, cross-account access, fine-grained IAM
   - Cons: $0.40/month per secret (~$1.60/month for 4 secrets), API call costs, added latency
   - Rejected: Cost not justified for current needs, rotation not required yet

2. **AWS Systems Manager Parameter Store**
   - Pros: Free for standard parameters, integrated with AWS, hierarchical structure
   - Cons: API call latency (cold start penalty), requires IAM permissions, more complex
   - Rejected: Adds complexity without significant benefit over environment variables

3. **External Secret Management (HashiCorp Vault, etc.)**
   - Pros: Advanced features, audit logging, dynamic secrets
   - Cons: Additional infrastructure, cost, operational complexity, network dependency
   - Rejected: Overkill for serverless Lambda application

4. **Hardcoded in Code**
   - Pros: Simplest approach, no runtime dependencies
   - Cons: Insecure, cannot be rotated without redeployment, visible in version control
   - Rejected: Security anti-pattern, not acceptable for production

**Decision Rationale**:

**Simplicity**:

- No additional AWS services required
- No API calls to fetch secrets (faster cold starts)
- Easy to update via SAM deployment

**Cost**:

- **Zero additional cost** (environment variables are free)
- Secrets Manager: ~$2/month for current secrets
- Parameter Store API calls: ~$0.05/10,000 calls

**Security**:

- Environment variables encrypted at rest by AWS Lambda
- Only accessible to Lambda execution role (IAM-controlled)
- Not visible in CloudWatch Logs (if handled correctly)
- Parameter files git-ignored (secrets never committed)

**Developer Experience**:

- Easy to update: edit parameter file and redeploy
- No code changes needed to rotate secrets
- Clear separation of config per environment (staging/production)
- Fast local development with `.env` files

**Trade-offs Accepted**:

- No automatic secret rotation (manual rotation required)
- No secret versioning (CloudFormation stack versions provide some history)
- Secrets visible in Lambda console (IAM controls access)
- No audit log of secret access (CloudWatch Logs track Lambda invocations)

**Consequences**:

**Positive**:

- Zero additional cost for secret storage
- Faster Lambda cold starts (no Secrets Manager API calls)
- Simple deployment process (secrets in parameter files)
- Easy to update secrets (redeploy with new parameters)
- No additional IAM permissions needed beyond Lambda execution role

**Negative**:

- Manual secret rotation (no automated rotation policies)
- Secrets visible in AWS Console Lambda configuration (IAM-protected)
- No built-in secret versioning (rely on git history for parameter files)
- If secrets leak, must rotate manually and redeploy

**Security Measures**:

- Parameter files with real secrets added to `.gitignore`
- Example parameter files (with placeholders) committed to git
- GitHub secrets used for CI/CD deployment (never in repository)
- Least-privilege IAM roles for Lambda execution
- Secrets not logged to CloudWatch Logs (careful logging practices)

**Future Migration Path**:
If compliance requirements change or automatic rotation is needed:

1. Migrate to AWS Secrets Manager (no application code changes)
2. Update SAM template to reference secrets ARNs
3. Add IAM permissions for Lambda to access Secrets Manager
4. Update Lambda code to fetch secrets from Secrets Manager (minimal changes)

**Implementation**:

- SAM template parameters: `GKey`, `OpenAIKey`, `XIKey`, `BucketNameCustomerData`, etc.
- Parameter files: `infrastructure/parameters/staging.json`, `production.json`
- Git-ignored parameter files contain real secrets
- Example parameter files committed with placeholder values
- GitHub Actions workflows use GitHub secrets to inject parameters

**Related ADRs**:

- ADR-0006: SAM Infrastructure as Code
- ADR-0003: Secrets Management (Phase 0)

**References**:

- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [AWS Secrets Manager Pricing](https://aws.amazon.com/secrets-manager/pricing/)
- [infrastructure/README.md](../infrastructure/README.md) - Parameter file documentation
