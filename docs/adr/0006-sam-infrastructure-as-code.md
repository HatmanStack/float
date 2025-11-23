# ADR-0006: SAM Infrastructure as Code

**Status**: Accepted

**Date**: 2025-11-19

**Context**: The Float meditation app backend was manually deployed through the AWS Console, requiring manual steps to install dependencies, create zip files, upload code, configure environment variables, and manage Lambda layers. This manual process was error-prone, time-consuming, and made it difficult to maintain environment parity between staging and production. Infrastructure changes required careful documentation and were difficult to version control or reproduce.

**Decision**: Use AWS SAM (Serverless Application Model) for infrastructure-as-code deployment of the backend Lambda function and all related AWS resources.

**Alternatives Considered**:

1. **AWS CDK (Cloud Development Kit)**
   - Pros: More flexible, programmatic infrastructure definition, supports multiple languages
   - Cons: More complex, steeper learning curve, overkill for simple Lambda deployment
   - Rejected: SAM is purpose-built for serverless and simpler for this use case

2. **Terraform**
   - Pros: Cloud-agnostic, mature ecosystem, strong state management
   - Cons: Not AWS-specific, more configuration required, separate state management
   - Rejected: Team already familiar with AWS, no multi-cloud requirement

3. **Serverless Framework**
   - Pros: Simple configuration, good plugin ecosystem, popular
   - Cons: Third-party dependency, less direct AWS integration than SAM
   - Rejected: SAM is AWS-native with better CloudFormation integration

4. **Continue Manual Deployment**
   - Pros: No new tools to learn, complete control
   - Cons: Error-prone, not repeatable, difficult to track changes
   - Rejected: Does not scale, high risk of configuration drift

**Consequences**:

**Positive**:

- All infrastructure defined in version-controlled code (`infrastructure/template.yaml`)
- Single-command deployment with guaranteed reproducibility
- Environment parity between staging and production (same template, different parameters)
- Easy rollback via CloudFormation stack updates
- Built-in validation with `sam validate`
- Local testing with `sam local` and Docker
- Automatic IAM role creation with least-privilege policies
- CloudFormation change sets for safe production deployments

**Negative**:

- Requires SAM CLI installation and Docker for local development
- Learning curve for SAM/CloudFormation syntax
- Deployment slower than manual zip upload (builds with Docker)
- Debugging SAM build issues can be challenging

**Implementation**:

- Single environment-agnostic SAM template (see ADR-0001)
- Parameter files for staging and production environments
- Automated deployment scripts with validation and error handling
- GitHub Actions integration for CI/CD automation

**Trade-offs Accepted**:

- Slower initial deployment (Docker build) for long-term reliability and consistency
- Additional tooling requirements (SAM CLI, Docker) for better automation
- CloudFormation abstractions vs. direct AWS API control

**Related ADRs**:

- ADR-0001: SAM Template Structure (Phase 0)
- ADR-0007: HTTP API Gateway (this decision)
- ADR-0008: Environment Variables for Secrets (this decision)

**References**:

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [infrastructure/README.md](../infrastructure/README.md) - Implementation details
- [infrastructure/DEPLOYMENT.md](../infrastructure/DEPLOYMENT.md) - Deployment guide
