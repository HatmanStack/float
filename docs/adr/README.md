# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Float meditation app project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help document the "why" behind technical choices.

## ADR Format

Each ADR includes:
- **Status**: Accepted, Rejected, Deprecated, or Superseded
- **Date**: When the decision was made
- **Context**: The situation and problem being addressed
- **Decision**: What was decided and why
- **Alternatives Considered**: Other options and why they were rejected
- **Consequences**: Positive and negative impacts of the decision
- **Related ADRs**: Links to related decisions

## Index of ADRs

### Phase 0 ADRs (Foundation)

These ADRs were defined in the planning phase and guided implementation:

| ADR | Title | Status | Phase |
|-----|-------|--------|-------|
| [ADR-0001](../plans/Phase-0.md#adr-1-sam-template-structure) | SAM Template Structure | Accepted | 0 |
| [ADR-0002](../plans/Phase-0.md#adr-2-api-gateway-choice---http-api-v2) | API Gateway Choice - HTTP API (v2) | Accepted | 0 |
| [ADR-0003](../plans/Phase-0.md#adr-3-secrets-management---environment-variables-in-sam) | Secrets Management - Environment Variables | Accepted | 0 |
| [ADR-0004](../plans/Phase-0.md#adr-4-ffmpeg-layer-management) | FFmpeg Layer Management | Accepted | 0 |
| [ADR-0005](../plans/Phase-0.md#adr-5-testing-strategy---layered-test-pyramid) | Testing Strategy - Layered Test Pyramid | Accepted | 0 |

### Phase 6 ADRs (Implementation)

These ADRs document decisions made during Phase 6 implementation:

| ADR | Title | Status | Phase |
|-----|-------|--------|-------|
| [ADR-0006](0006-sam-infrastructure-as-code.md) | SAM Infrastructure as Code | Accepted | 6 |
| [ADR-0007](0007-http-api-gateway.md) | HTTP API Gateway Choice | Accepted | 6 |
| [ADR-0008](0008-environment-variables-secrets.md) | Environment Variables for Secrets | Accepted | 6 |
| [ADR-0009](0009-comprehensive-testing-strategy.md) | Comprehensive Testing Strategy | Accepted | 6 |
| [ADR-0010](0010-e2e-testing-framework.md) | E2E Testing Framework (Detox) | Accepted | 6 |

## How to Use ADRs

### For Developers

When working on the project:
1. **Before making architectural changes**: Review related ADRs to understand past decisions
2. **When questioning a design**: Check if an ADR explains the rationale
3. **If architecture evolves**: Update or supersede existing ADRs

### For New Contributors

Start here to understand key architectural decisions:
1. Read [ADR-0006](0006-sam-infrastructure-as-code.md) - Why we use SAM
2. Read [ADR-0009](0009-comprehensive-testing-strategy.md) - Testing approach
3. Read [ADR-0010](0010-e2e-testing-framework.md) - E2E testing with Detox

### For Code Reviews

When reviewing PRs:
- Check if changes align with existing ADRs
- Suggest creating new ADR for significant architectural changes
- Update ADRs if decisions change

## Creating a New ADR

To create a new ADR:

1. Copy the template below
2. Number it sequentially (0011, 0012, etc.)
3. Fill in all sections
4. Submit as part of your PR
5. Update this README index

### ADR Template

```markdown
# ADR-XXXX: Decision Title

**Status**: Proposed | Accepted | Rejected | Deprecated | Superseded

**Date**: YYYY-MM-DD

**Context**: Describe the situation and problem being addressed.

**Decision**: State the decision and explain why.

**Alternatives Considered**:
1. **Alternative 1**: Pros, cons, why rejected
2. **Alternative 2**: Pros, cons, why rejected

**Consequences**:

**Positive**:
- Benefit 1
- Benefit 2

**Negative**:
- Trade-off 1
- Trade-off 2

**Implementation**: How the decision is being implemented.

**Related ADRs**: Links to related decisions.

**References**: Links to documentation, articles, etc.
```

## ADR Lifecycle

- **Proposed**: Under discussion, not yet accepted
- **Accepted**: Decision made and being implemented
- **Rejected**: Proposed but decided against
- **Deprecated**: No longer relevant but kept for history
- **Superseded**: Replaced by a newer ADR (link to new ADR)

## Questions?

For questions about ADRs or architectural decisions:
- Create a GitHub issue
- Ask in pull request comments
- Refer to [docs/ARCHITECTURE.md](../ARCHITECTURE.md) for system overview
