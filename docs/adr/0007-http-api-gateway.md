# ADR-0007: HTTP API Gateway Choice

**Status**: Accepted

**Date**: 2025-11-19

**Context**: The Float backend Lambda function needs an HTTP endpoint for the React Native frontend to invoke. AWS offers multiple options: REST API (v1), HTTP API (v2), and Lambda Function URLs. The Lambda was previously accessed directly (likely via Function URLs or manual invocation), but we needed a production-ready API solution with proper CORS support, monitoring, and throttling.

**Decision**: Use AWS API Gateway HTTP API (v2) instead of REST API (v1) or Lambda Function URLs.

**Alternatives Considered**:

1. **REST API (API Gateway v1)**
   - Pros: More features (API keys, usage plans, request/response transformation, caching)
   - Cons: 70% more expensive ($3.50 vs $1.00 per million requests), slower, more complex
   - Rejected: Advanced features not needed, cost difference significant at scale

2. **Lambda Function URLs**
   - Pros: Simplest setup, no additional cost, fastest performance
   - Cons: Limited monitoring, no throttling, no API management, basic CORS
   - Rejected: Not robust enough for production, lacks proper API management

3. **Application Load Balancer (ALB)**
   - Pros: Can route to multiple targets, good for microservices
   - Cons: More expensive for single Lambda, overkill for this use case, requires VPC
   - Rejected: Unnecessary complexity and cost for single Lambda function

**Decision Rationale**:

**Cost Savings**:
- HTTP API: $1.00 per million requests
- REST API: $3.50 per million requests
- **70% cost reduction** at scale

**Sufficient Features**:
- Built-in CORS support (complements existing Lambda middleware)
- JWT authorizers (if needed in future)
- CloudWatch metrics and logging
- Request throttling and quotas
- Custom domain support
- Good enough for Float's simple POST endpoint routing

**Performance**:
- Lower latency than REST API
- Faster cold starts
- Direct Lambda proxy integration

**Trade-offs Accepted**:
- No API keys (not needed - no third-party API access)
- No usage plans (not needed - no tiered pricing)
- No request/response transformation (Lambda handles this)
- No caching (Lambda is fast enough, S3 provides storage)

**Consequences**:

**Positive**:
- 70% cost savings on API Gateway requests
- Simpler configuration in SAM template
- Faster API response times
- Built-in CORS eliminates CORS preflight issues
- CloudWatch integration for monitoring
- Custom domain support for production

**Negative**:
- Cannot implement API keys in future without migration
- No built-in caching (must implement in Lambda/S3 if needed)
- Fewer API management features if requirements change

**Future Considerations**:
- If API keys become required → migrate to REST API (breaking change)
- If multiple microservices → consider ALB or API Gateway custom domains
- If caching needed → implement CloudFront or Lambda-level caching first

**Implementation**:
- HTTP API defined in `infrastructure/template.yaml`
- Single `POST /meditation` route (proxy to Lambda)
- CORS configured for all origins (development and production)
- CloudWatch Logs enabled by default
- No authorizer initially (can add JWT in future)

**Related ADRs**:
- ADR-0006: SAM Infrastructure as Code
- ADR-0003: Secrets Management (Phase 0)

**References**:
- [AWS HTTP API vs REST API Comparison](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)
- [HTTP API Pricing](https://aws.amazon.com/api-gateway/pricing/)
