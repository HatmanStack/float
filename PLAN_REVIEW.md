# Plan Review - Tech Lead Assessment

**Review Date:** 2025-11-18
**Reviewer:** Tech Lead
**Plan Location:** `docs/plans/`
**Total Phases:** 7 (Phase 0-6)
**Estimated Tokens:** ~155,000

---

## Executive Summary

The implementation plan demonstrates strong technical depth with comprehensive Phase-0 foundation, well-structured tasks, and detailed verification checklists. **However, there are 5 critical gaps that will block a zero-context engineer.**

**Status:** ❌ **CONDITIONAL APPROVAL - Fix Critical Issues First**

---

## Plan Structure Review

✅ **PASS** - Complete plan structure:
- README.md exists with overview, prerequisites, phase summary
- Phase-0.md exists with architecture decisions, shared patterns, testing strategy
- Phase files numbered sequentially (Phase-1 through Phase-6)
- All required sections present

✅ **PASS** - Task clarity:
- 58 task-level token estimates provided
- 51 verification checklists included
- 51 commit message templates provided
- 51 testing instruction blocks included
- No TODO/FIXME/TBD placeholders found

✅ **PASS** - Scope appropriateness:
- Phase-0: ~5,000 tokens (foundation)
- Phase-1: ~25,000 tokens (SAM infrastructure)
- Phase-2: ~30,000 tokens (backend core tests)
- Phase-3: ~25,000 tokens (backend integration/E2E)
- Phase-4: ~30,000 tokens (frontend component tests)
- Phase-5: ~25,000 tokens (frontend integration/E2E)
- Phase-6: ~15,000 tokens (CI/CD + docs)
- **Total: ~155,000 tokens** (reasonable for context window)

✅ **PASS** - Codebase verification:
- Backend structure matches plan expectations (38 Python files)
- Frontend structure verified (25 TypeScript components)
- 7 existing component test files confirmed
- GitHub Actions workflows exist (backend-tests.yml, frontend-tests.yml)
- No infrastructure/ directory yet (to be created in Phase 1)

---

## Critical Issues (Must Fix)

### 1. **Phase-0: Missing Objective Completion Criteria** ❌

**Location:** `docs/plans/Phase-0.md:567-577`

**Issue:** Phase-0 completion criteria are subjective and not actionable:
```markdown
This phase is complete when:
- All ADRs are reviewed and understood
- Testing strategy is clear
- Team (or engineer) is ready to begin Phase 1
```

**Problem:** A zero-context engineer won't know when they're "done understanding." What does "clear" mean? How do they confirm they're "ready"? This is not verifiable.

**Impact:** Engineer may skip critical foundational knowledge or waste time re-reading, uncertain if they should proceed.

**Recommended Fix:**
```markdown
## Phase Completion

This phase is complete when you can answer YES to all checkpoints:

**Verification Checkpoints:**
- [ ] I have read all 8 ADRs (ADR-1 through ADR-8)
- [ ] I have read the Backend Testing Strategy section (lines 221-285)
- [ ] I have read the Frontend Testing Strategy section (lines 287-349)
- [ ] I have read the Coding Conventions sections (Backend + Frontend)
- [ ] I have read the Common Pitfalls sections (Backend, Frontend, SAM/Infrastructure)
- [ ] I can answer: "What is our SAM template structure?" (Answer: ADR-1)
- [ ] I can answer: "What testing pyramid do we follow?" (Answer: ADR-5, 70% unit, 20% integration, 10% E2E)
- [ ] I can answer: "What API Gateway type are we using?" (Answer: ADR-2, HTTP API v2)
- [ ] I understand the TDD workflow (lines 550-563)

**Self-Assessment Questions:**
1. If a test fails due to mock leakage, where would I look? (Answer: Backend Pitfall #2, line 446)
2. What commit message format should I use? (Answer: Conventional Commits, ADR-8, line 178)
3. Where do API keys go in SAM? (Answer: Environment variables, ADR-3, line 63)

If you can answer these questions, proceed to Phase 1. If not, review the relevant sections.

No code changes or tests are created in this phase.
```

---

### 2. **Phase-1: FFmpeg Layer Creation Not Documented** ❌

**Location:** Multiple references across `Phase-1.md`, `Phase-0.md:85-98`, `README.md:25`

**Issue:** Phase 1 requires "FFmpeg Lambda layer ARN available" as prerequisite (Phase-1.md:22), but there is **ZERO documentation** on:
- How to create the FFmpeg layer
- Where to find build scripts
- What FFmpeg version to use
- How to test the layer works
- What to do if layer doesn't exist

**Current guidance:**
- Phase-0.md:96: "Layer update process documented separately"
- Phase-0.md:97: "If layer doesn't exist, provide clear error message with creation instructions"

**Problem:** WHERE is it documented separately? The implementer will be **BLOCKED** at Phase-1, Task-8 (Deploy to Staging) with deployment failure: "Layer version arn:aws:lambda:us-east-1:123456789012:layer:ffmpeg:1 does not exist."

**Impact:** Complete blocker. Engineer cannot proceed without FFmpeg layer. They'll need to:
1. Research FFmpeg Lambda layers (2k+ tokens)
2. Find or build FFmpeg binary (3k+ tokens)
3. Package as Lambda layer (2k+ tokens)
4. Debug compatibility issues (2k+ tokens)
5. **Potential 10k+ token detour from plan**

**Recommended Fix:** Add to Phase-0 after ADR-8:

```markdown
---

### ADR-9: FFmpeg Lambda Layer - External Dependency

**Decision:** Use pre-built FFmpeg Lambda layer; document setup process for new environments.

**Rationale:**
- FFmpeg compilation is complex and time-consuming
- Layer is stable and changes infrequently
- Separate lifecycle from application code

**Setup Process:**

**Option 1: Use Existing Layer (Recommended)**
If FFmpeg layer already exists in your AWS account:
1. Find layer ARN: `aws lambda list-layer-versions --layer-name ffmpeg --region us-east-1`
2. Copy ARN for parameter file: `arn:aws:lambda:us-east-1:ACCOUNT_ID:layer:ffmpeg:VERSION`
3. Skip to Phase 1

**Option 2: Use Public FFmpeg Layer**
Use community-maintained layer:
1. Layer ARN: `arn:aws:lambda:us-east-1:XXXXXXXXXX:layer:ffmpeg:1`
2. **WARNING:** Verify compatibility with Python 3.12 and x86_64 architecture
3. Test before using in production

**Option 3: Build FFmpeg Layer (Advanced)**
If you must build from scratch:

1. Clone FFmpeg layer build repository:
   ```bash
   git clone https://github.com/serverlesspub/ffmpeg-aws-lambda-layer
   cd ffmpeg-aws-lambda-layer
   ```

2. Build layer using Docker:
   ```bash
   docker build -t ffmpeg-layer .
   ./package.sh
   ```

3. Deploy layer to AWS:
   ```bash
   aws lambda publish-layer-version \
     --layer-name ffmpeg \
     --description "FFmpeg for audio processing" \
     --zip-file fileb://layer.zip \
     --compatible-runtimes python3.12 \
     --region us-east-1
   ```

4. Save the returned LayerVersionArn for parameter files

5. Test layer works:
   ```bash
   # Create test Lambda
   # Attach layer
   # Run: /opt/bin/ffmpeg -version
   # Should output: ffmpeg version X.X.X
   ```

**Verification:**
- FFmpeg binary exists at `/opt/bin/ffmpeg`
- Version is 4.x or newer
- Architecture matches Lambda (x86_64)

**Troubleshooting:**
- "Layer not found": Check region matches Lambda function region
- "Binary not found": Verify layer path is `/opt/bin/ffmpeg` not `/opt/ffmpeg`
- "Permission denied": Layer must be compatible with Lambda runtime

---
```

Update Phase-1.md Prerequisites:
```markdown
## Prerequisites

- Phase 0 reviewed and understood
- AWS SAM CLI installed (`sam --version`)
- AWS CLI configured with credentials (`aws configure list`)
- **FFmpeg Lambda layer ARN available (see Phase-0 ADR-9 for setup)**
  - If not available, complete ADR-9 setup before starting Phase 1
  - Have layer ARN ready for both staging and production
- API keys ready for staging environment (Google Gemini, OpenAI, ElevenLabs)
- Docker installed (for local SAM testing)
```

---

### 3. **Phase-1, Task-3: S3 Bucket Name Collision Not Addressed** ❌

**Location:** `docs/plans/Phase-1.md:140-203` (Task 3: Add S3 Bucket Resources)

**Issue:** SAM template will create S3 buckets using parameter-provided names, but no guidance on handling global name collisions.

**Current guidance:**
- Line 156: "Bucket names use parameters with environment suffix"
- Line 188: "Verify bucket naming will be unique (include account ID or random suffix if needed)"

**Problem:** S3 bucket names are **globally unique across all AWS accounts**. If bucket name `float-cust-data-staging` exists in ANY AWS account worldwide, CloudFormation deployment will fail with:

```
CREATE_FAILED: float-cust-data-staging already exists
```

A zero-context engineer won't understand:
1. Why deployment failed
2. That S3 names are globally unique (not just account-unique)
3. How to fix it (can't just retry)
4. What naming strategy ensures uniqueness

**Impact:** Deployment failure at Phase-1, Task-8. Engineer will debug CloudFormation events, search for solution, potentially waste 2-5k tokens.

**Recommended Fix:** Update Phase-1, Task-3 Implementation Steps:

```markdown
**Implementation Steps:**

1. Add S3 bucket parameters to Parameters section:
   - Customer data bucket name parameter
   - Audio bucket name parameter

2. **IMPORTANT - Bucket Naming Strategy:**
   S3 bucket names are globally unique across ALL AWS accounts. To avoid collisions:

   **Option A: Include AWS Account ID (Recommended)**
   ```yaml
   CustomerDataBucket:
     Type: AWS::S3::Bucket
     Properties:
       BucketName: !Sub '${AWS::StackName}-cust-data-${AWS::AccountId}'
   ```
   Result: `float-meditation-staging-cust-data-123456789012`

   **Option B: Use CloudFormation-generated names**
   ```yaml
   CustomerDataBucket:
     Type: AWS::S3::Bucket
     # No BucketName property - CloudFormation generates unique name
   ```
   Result: `float-meditation-staging-customerdatabucket-a1b2c3d4e5f6`

   **Option C: Use parameter with account ID suffix**
   - Parameter file: `"CustomerDataBucketName": "float-cust-data-staging-123456789012"`
   - Requires manual account ID entry

   **Recommendation:** Use Option A for predictable, unique names.

3. Add two S3 bucket resources to Resources section:
   - Customer data bucket (stores user data, summaries, meditation records)
   - Audio bucket (stores generated meditation audio files)

4. Configure bucket properties:
   - Encryption: AES256 (server-side encryption enabled by default)
   - Versioning: Consider enabling for production data recovery
   - Lifecycle policies: Consider adding expiration rules for cost optimization
   - Access control: Private access only

5. Add bucket policies if needed for cross-service access

6. Update Lambda execution role to grant S3 permissions:
   - s3:PutObject for both buckets
   - s3:GetObject for both buckets
   - s3:DeleteObject for both buckets
   - Scope permissions to specific bucket ARNs
```

Update Verification Checklist:
```markdown
**Verification Checklist:**
- [ ] Two S3 bucket resources defined (customer data and audio)
- [ ] Bucket names use CloudFormation intrinsic functions for uniqueness (!Sub with ${AWS::AccountId})
- [ ] OR BucketName property omitted (CloudFormation generates unique name)
- [ ] Server-side encryption enabled
- [ ] Lambda execution role has appropriate S3 permissions
- [ ] Bucket ARNs exported as outputs for reference
- [ ] Template still validates successfully
- [ ] Bucket naming documented in parameter file examples with account ID
```

Update Testing Instructions:
```markdown
**Testing Instructions:**
- Run `sam validate` to ensure template is still valid
- Review IAM permissions to ensure they follow least-privilege principle
- Verify bucket naming strategy prevents global name collisions:
  ```bash
  # Check what bucket names will be created
  aws cloudformation describe-stack-resources \
    --stack-name float-meditation-staging \
    --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId'
  ```
- If deployment fails with "bucket already exists":
  - Change bucket naming strategy to Option A or B above
  - OR change ParameterValue in staging.json to include unique suffix
```

---

### 4. **Phase-5: E2E Framework Decision Deferred** ⚠️

**Location:** `docs/plans/Phase-5.md:9` and throughout Phase-5 tasks

**Issue:** Phase-5 mentions "E2E testing framework (Detox or similar)" and "set up end-to-end testing infrastructure," but Phase-0 doesn't make this architectural decision.

**Current state:**
- Phase-0: No ADR for E2E framework choice
- Phase-5.md:9: "E2E testing framework set up (Detox or similar)"
- README.md:64: "sets up end-to-end testing framework (Detox or similar)"

**Problem:** Choosing E2E framework is a **MAJOR architectural decision** that affects:

1. **Build configuration:** Detox requires native builds; Maestro doesn't
2. **CI/CD setup:** iOS vs Android simulators, emulator management
3. **Test structure:** Detox uses gray-box testing; Appium uses black-box
4. **Developer workflow:** Detox requires Xcode/Android Studio; Maestro doesn't
5. **Token budget:** Framework setup could be 5k-8k tokens

**Impact:** Engineer will hit Phase-5, Task-1 and need to:
1. Research Detox vs Maestro vs Appium vs WebDriverIO (2k tokens)
2. Read documentation and compare features (2k tokens)
3. Install and configure chosen framework (3k tokens)
4. Debug setup issues (2k+ tokens)
5. **Potential 10k+ token detour before writing first E2E test**

This violates the principle of "all architectural decisions in Phase-0."

**Recommended Fix:** Add to Phase-0 as new ADR after ADR-8:

```markdown
---

### ADR-9: E2E Testing Framework - Detox

**Decision:** Use Detox for React Native end-to-end testing.

**Rationale:**
- **Native React Native support:** Built specifically for React Native (no WebViews or bridges needed)
- **Gray-box testing:** Can access React Native internals for faster, more reliable tests
- **Automatic synchronization:** Waits for React Native to be idle (no manual waits)
- **Cross-platform:** Works with both iOS and Android
- **Active development:** Maintained by Wix, good community support
- **Integrates with Jest:** Familiar testing patterns

**Trade-offs:**
- **Requires native builds:** Slower CI builds (need to compile iOS/Android apps)
- **More complex setup:** Requires Xcode or Android Studio for local development
- **Learning curve:** More complex than pure JavaScript solutions
- **CI resource requirements:** Needs macOS runners for iOS tests (expensive)

**Alternatives Considered:**

1. **Maestro**
   - Pros: Simpler setup, no native builds, easier debugging
   - Cons: Newer tool (less mature), less control over RN internals, YAML syntax
   - Rejected: Less ecosystem support, uncertain long-term maintenance

2. **Appium**
   - Pros: Cross-platform (mobile + web), industry standard, WebDriver protocol
   - Cons: Slower (WebDriver overhead), more complex setup, not RN-specific
   - Rejected: Overkill for RN-only app, slower test execution

3. **Playwright (experimental RN support)**
   - Cons: RN support still experimental, better suited for web
   - Rejected: Not mature enough for React Native

**Implementation Plan (Phase 5):**
- Install Detox and dependencies
- Configure for iOS simulator (local development)
- Configure for Android emulator (CI/CD on Linux)
- Use Detox matchers: `by.id()`, `by.text()`, `by.type()`
- Run E2E tests in CI on Android only (cost efficiency)
- Document iOS E2E testing for manual testing

**Testing Strategy:**
- E2E tests represent 10% of total test suite (per ADR-5)
- Focus on critical user flows only:
  - Authentication flow (sign in, sign out)
  - Recording flow (record audio, submit)
  - Meditation generation flow (generate, play, save)
- Integration tests cover component interactions
- Unit tests cover business logic

**Configuration:**
- Test on Android API 31+ (Linux CI runners)
- Test on iOS 15+ (local development only)
- Use release builds for E2E tests (matches production)
- Mock backend API for E2E tests (deterministic results)

---
```

Update Phase-5.md title and prerequisites:
```markdown
# Phase 5: Frontend Test Improvements - Integration & E2E (Detox)

## Prerequisites

- Phase 4 complete (component tests at 75%+ coverage)
- **Phase 0 ADR-9 reviewed (E2E framework decision: Detox)**
- Understanding of React Context API usage in the app
- Understanding of navigation structure
- Familiarity with E2E testing concepts
- Review existing Context providers in `context/` directory
- **Android Studio installed (for Android emulator) OR Xcode installed (for iOS simulator)**
```

Update Phase-5, Task-3 to be specific:
```markdown
### Task 3: Set Up Detox E2E Testing Framework

**Goal:** Install and configure Detox for React Native E2E testing, following ADR-9.
```

---

### 5. **Phase-1, Task-6: Parameter File Security Risk** ⚠️

**Location:** `docs/plans/Phase-1.md:339-415` (Task 6: Create Environment Parameter Files)

**Issue:** Task 6 instructs creating `staging.json` with real API keys, but verification of `.gitignore` happens in same task. Risk of accidental commit if `.gitignore` isn't working.

**Current instruction (line 361-365):**
```markdown
2. Create actual staging.json with real values:
   - Real API keys for staging environment
   - Real FFmpeg layer ARN
   - Real bucket names (with -staging suffix)
   - Appropriate environment name: "staging"
```

**Problem:** This asks engineer to create a file with **REAL API KEYS and SECRET VALUES** on first attempt. If:
- `.gitignore` has typo (Task 1, created 5 tasks ago)
- Engineer forgets to test `.gitignore`
- Git caching issue (file tracked before `.gitignore` added)
- Engineer runs `git add .` by habit

Then secrets are committed to repository. This is a **security incident**.

**Impact:**
- API key exposure (must rotate all keys)
- Potential unauthorized AWS access
- Security compliance violation
- Requires history rewrite to remove secrets

**Recommended Fix:** Update Phase-1, Task-6 Implementation Steps:

```markdown
**Implementation Steps:**

1. Create example parameter files with placeholder values:
   - Use "YOUR_API_KEY_HERE" for API keys
   - Use "arn:aws:lambda:REGION:ACCOUNT:layer:ffmpeg:VERSION" for layer ARN
   - Use "float-cust-data-staging-ACCOUNT_ID" for bucket names
   - Include all parameters defined in template
   - Include comments explaining each parameter

2. **SECURITY CHECKPOINT - Verify .gitignore before creating real parameter file:**

   ```bash
   # Test that .gitignore works BEFORE adding real secrets
   cd infrastructure/parameters/

   # Create test file with fake secret
   echo '{"test": "secret"}' > test-secret.json

   # Check git status
   git status

   # EXPECTED: test-secret.json should NOT appear in output
   # If it appears in "Untracked files", STOP - .gitignore is broken

   # Also verify example files ARE tracked
   git status staging-example.json
   # EXPECTED: Should show as tracked or staged

   # Clean up test file
   rm test-secret.json

   # If .gitignore test fails, go back to Task 1 and fix .gitignore
   # DO NOT PROCEED until .gitignore works correctly
   ```

3. Create actual staging.json with real values **ONLY after .gitignore verified:**
   - Copy staging-example.json: `cp staging-example.json staging.json`
   - Replace placeholder values with real API keys
   - **IMMEDIATELY verify not tracked:** `git status` (should not list staging.json)
   - Fill in real FFmpeg layer ARN (from Phase-0 ADR-9 setup)
   - Fill in real bucket names (with -staging suffix and account ID)
   - Set environment name: "staging"

4. **Double-check security:**
   ```bash
   # Verify staging.json is ignored
   git status
   git ls-files | grep staging.json
   # Should return nothing

   # Verify example files are tracked
   git ls-files | grep example.json
   # Should show staging-example.json and production-example.json
   ```

5. Document parameter file format in infrastructure/README.md
```

Update Verification Checklist:
```markdown
**Verification Checklist:**
- [ ] Example parameter files exist and are tracked by git
- [ ] .gitignore test passed (test-secret.json was ignored)
- [ ] staging.json exists with real values
- [ ] staging.json is git-ignored (`git status` does not list it)
- [ ] staging.json is NOT in git index (`git ls-files | grep staging.json` returns nothing)
- [ ] All template parameters have corresponding entries in parameter files
- [ ] Example files have clear placeholder values (not real secrets)
- [ ] README.md documents parameter file usage
```

Add new Common Pitfall to Phase-0:
```markdown
6. **Committing Secrets to Git:**
   - ALWAYS test .gitignore before creating files with real secrets
   - Create test file first, verify it's ignored, then create real file
   - Use `git status` and `git ls-files` to double-check
   - Never use `git add .` without reviewing what's staged
   - If secrets committed: rotate ALL secrets immediately, rewrite history
```

---

## Suggestions (Nice to Have)

### 1. **Phase-1: Add Deployment Rollback Guidance**

**Location:** `Phase-1.md:508-576` (Task 8: Deploy to Staging Environment)

**Suggestion:** Task 8 deploys to staging but doesn't explain what to do if deployment fails halfway through.

Add to Task-8 Implementation Steps:
```markdown
6. If deployment fails:

   **Debugging Failed Deployments:**
   1. Check CloudFormation Events:
      ```bash
      aws cloudformation describe-stack-events \
        --stack-name float-meditation-staging \
        --max-items 20
      ```

   2. Look for "CREATE_FAILED" or "UPDATE_FAILED" events

   3. Common failure scenarios:

      **FFmpeg layer ARN invalid:**
      - Error: "Layer version arn:... does not exist"
      - Fix: Verify layer exists: `aws lambda get-layer-version --arn [ARN]`
      - Fix: Check region matches (layer must be in same region as Lambda)
      - Fix: See Phase-0 ADR-9 for layer setup

      **S3 bucket name taken:**
      - Error: "Bucket name already exists"
      - Fix: S3 names are globally unique - change bucket names in staging.json
      - Fix: Add account ID suffix (see Phase-1, Task-3 guidance)

      **IAM permissions insufficient:**
      - Error: "User is not authorized to perform: iam:CreateRole"
      - Fix: Ensure AWS credentials have CloudFormation/Lambda/S3/IAM permissions
      - Fix: Add `--capabilities CAPABILITY_IAM` to deploy command (should be default)

      **Parameter validation error:**
      - Error: "Parameter validation failed"
      - Fix: Check all required parameters present in staging.json
      - Fix: Verify parameter types match template (string vs number)

   4. Rollback behavior:
      - CloudFormation automatically rolls back on failure
      - All created resources are deleted
      - Stack state returns to previous working state (or DELETE_COMPLETE if first deploy)

   5. To retry after fixing issue:
      ```bash
      # Fix the parameter file or template
      # Then re-run deployment
      ./infrastructure/scripts/deploy-staging.sh
      ```

   6. To manually delete failed stack:
      ```bash
      aws cloudformation delete-stack --stack-name float-meditation-staging
      # Wait for deletion
      aws cloudformation wait stack-delete-complete --stack-name float-meditation-staging
      ```

   7. Check CloudFormation console for visual debugging:
      - AWS Console → CloudFormation → float-meditation-staging
      - Events tab shows detailed error messages
      - Resources tab shows which resources failed
```

---

### 2. **Phase-2 through Phase-5: Token Estimates May Be Low**

**Observation:** Each testing phase (2-5) is estimated at 25-30k tokens with 7-9 tasks each. Some individual tasks might exceed estimates:

- **Phase-2, Task-3:** "Expand AI Service Tests to 80%+ coverage" - currently at 59%, significant new tests needed
- **Phase-4, Task-1 & Task-2:** Debugging failing tests can be unpredictable (could be 2k tokens or 8k tokens depending on root cause)
- **Phase-5, Task-3:** Setting up Detox (even with ADR-9) could be 5k+ tokens due to native build complexity

**Suggestion:** Add buffer note to README:

```markdown
## Token Budget Notes

**Baseline Estimates:** ~155,000 tokens across all phases

**Contingency Planning:**
- Individual tasks may exceed estimates if debugging is required
- Estimates assume tests can be fixed/written without major code refactoring
- If component needs significant changes to be testable, task may grow 2-3x
- E2E framework setup (Phase 5) may require additional debugging (budget +5k tokens)
- Integration tests (Phase 3, 5) may hit API rate limits requiring retry logic (+2k tokens)

**Recommended Budget:** 175,000 - 200,000 tokens (includes 15-20% contingency)

**If Budget Exceeded:**
- Complete current phase before stopping
- Phases 1-3 are highest priority (infrastructure + backend)
- Phases 4-5 (frontend tests) can be deferred if needed
- Phase 6 (CI/CD) can be done incrementally
```

---

### 3. **Phase-6: Production Deployment Timing Unclear**

**Location:** `Phase-6.md` and `Phase-1.md:717` (Known Limitations)

**Observation:** Phase-1 notes "Production environment not yet deployed (will be done in Phase 6)". But Phase-6 focuses on CI/CD integration and documentation—no explicit production deployment task.

**Suggestion:** Add explicit task to Phase-6:

```markdown
### Task 0: Deploy SAM Stack to Production Environment

**Goal:** Deploy the SAM infrastructure to production AWS environment using the production parameter file, following ADR-7 manual deployment requirement.

**Files to Create:**
- `infrastructure/parameters/production.json` - Production parameters (git-ignored)

**Prerequisites:**
- Phase 1-5 complete
- Staging deployment verified and stable for at least 1 week
- Production AWS account/region confirmed
- Production API keys obtained (Google Gemini, OpenAI, ElevenLabs)
- Production FFmpeg layer deployed to production AWS account
- Stakeholder approval for production deployment

**Implementation Steps:**

1. Create production parameter file:
   - Copy production-example.json to production.json
   - Verify .gitignore excludes production.json
   - Fill in production API keys
   - Fill in production FFmpeg layer ARN
   - Use production bucket names (with -production suffix and account ID)
   - Set environment: "production"
   - Double-check all values are production-appropriate

2. Review production deployment plan:
   - Run SAM validate: `./infrastructure/scripts/validate-template.sh`
   - Review deployment script: `cat ./infrastructure/scripts/deploy-production.sh`
   - Verify script has safety confirmations
   - Understand rollback plan

3. Create CloudFormation change set (dry-run):
   - Modify deploy-production.sh to create change set only:
   ```bash
   sam deploy --no-execute-changeset \
     --template-file template.yaml \
     --parameter-overrides file://parameters/production.json
   ```
   - Review change set in AWS Console
   - Verify all resources are correct
   - Get stakeholder approval for changes

4. Execute production deployment:
   - Run deployment script: `./infrastructure/scripts/deploy-production.sh`
   - Confirm safety prompts
   - Monitor CloudFormation Events in AWS Console
   - Wait for CREATE_COMPLETE status

5. Verify production deployment:
   - Check Lambda function: `aws lambda get-function --function-name float-meditation-production`
   - Check S3 buckets: `aws s3 ls | grep production`
   - Check API Gateway: Get endpoint from stack outputs
   - Verify environment variables in Lambda console

6. Run production smoke tests:
   - Test summary request:
   ```bash
   curl -X POST https://[production-api-endpoint]/meditation \
     -H "Content-Type: application/json" \
     -d '{"type":"summary","user_id":"smoke-test","prompt":"test","audio":"NotAvailable"}'
   ```
   - Verify response is valid JSON with expected fields
   - Check S3 bucket for created files
   - Check CloudWatch Logs for successful execution

7. Update documentation:
   - Document production endpoint URL
   - Document production stack name
   - Add production deployment to infrastructure/README.md
   - Update ADR-7 with production deployment date

**Verification Checklist:**
- [ ] Production parameter file created and git-ignored
- [ ] CloudFormation change set reviewed and approved
- [ ] Production stack deployed successfully
- [ ] Lambda function configured correctly (4GB memory, 15min timeout)
- [ ] S3 buckets created with production names
- [ ] API Gateway endpoint accessible
- [ ] Environment variables configured
- [ ] FFmpeg layer attached
- [ ] Smoke tests passed
- [ ] Production endpoint documented

**Testing Instructions:**
```bash
# Verify production stack exists
aws cloudformation describe-stacks --stack-name float-meditation-production

# Test production endpoint
curl -X POST https://[prod-endpoint]/meditation \
  -H "Content-Type: application/json" \
  -d @infrastructure/test-requests/summary-request.json

# Check logs
aws logs tail /aws/lambda/float-meditation-production --follow

# Verify S3 files created
aws s3 ls s3://float-cust-data-production-[ACCOUNT_ID]/ --recursive | head -10
```

**Commit Message Template:**
```
feat(infrastructure): deploy SAM stack to production

- Create production.json parameter file (git-ignored)
- Deploy CloudFormation stack: float-meditation-production
- Verify Lambda, S3, API Gateway resources
- Run production smoke tests
- Document production endpoint and configuration

Production deployment completed successfully.
```

**Estimated Tokens:** ~3,000

---
```

Insert this as Task 0 before current Task 1 in Phase-6.md.

---

### 4. **Phase-0: Hardcoded Branch Name**

**Location:** `Phase-0.md:527, 546`

**Issue:** Development workflow contains hardcoded git branch: `claude/sam-deployment-testing-01KSjcbwLqaXQJQ8c9JQrV9h`

**Suggestion:** Replace with placeholder:

```markdown
1. **Start of Day:**
   - Pull latest changes: `git pull origin <your-feature-branch>`
   - Check CI/CD status for any failures
   - Review current phase checklist

...

4. **End of Day/Task:**
   - Push changes: `git push -u origin <your-feature-branch>`
   - Update phase checklist
   - Document any blockers or questions
```

---

## Phase-by-Phase Assessment

### Phase 0: Foundation ✅ (with fixes needed)
- **Structure:** Excellent - 8 ADRs covering all major decisions
- **Testing Strategy:** Comprehensive - backend + frontend strategies documented
- **Issues:** Completion criteria too subjective, FFmpeg layer not documented, E2E framework decision missing
- **Fix:** Add objective checkpoints, ADR-9 (FFmpeg), ADR-10 (Detox)

### Phase 1: SAM Infrastructure Setup ✅ (with fixes needed)
- **Structure:** Well-organized 9 tasks from directory setup to deployment verification
- **Token Estimate:** 25k reasonable for infrastructure setup
- **Issues:** S3 bucket collision not addressed, parameter file security risk
- **Fix:** Add bucket naming guidance, add .gitignore security checkpoint

### Phase 2: Backend Test Improvements - Core Coverage ✅
- **Structure:** 9 tasks covering Lambda handler, middleware, services, models, utils
- **Token Estimate:** 30k reasonable (significant test writing)
- **Completeness:** Comprehensive coverage targets (60%+ handler, 80%+ services)
- **No major issues** - well-structured and actionable

### Phase 3: Backend Test Improvements - Integration & E2E ✅
- **Structure:** 8 tasks for integration test infrastructure and real API testing
- **Token Estimate:** 25k reasonable
- **Completeness:** Covers Gemini, OpenAI, S3, audio processing, E2E flows
- **Minor:** Integration tests may hit API rate limits (suggest retry logic in plan)

### Phase 4: Frontend Test Improvements - Fix & Expand ✅
- **Structure:** 9 tasks fixing existing tests and adding component coverage
- **Token Estimate:** 30k reasonable (debugging unpredictable)
- **Completeness:** Covers all 12+ components systematically
- **Minor:** Debugging tasks (1-2) may exceed estimates depending on root cause

### Phase 5: Frontend Test Improvements - Integration & E2E ⚠️
- **Structure:** 8 tasks for integration and E2E testing
- **Token Estimate:** 25k may be low (E2E setup complex)
- **Issue:** E2E framework decision deferred ("Detox or similar")
- **Fix:** Add ADR-9 in Phase-0, make Phase-5 Detox-specific

### Phase 6: CI/CD Integration & Documentation ⚠️
- **Structure:** 8 tasks for GitHub Actions, documentation, final verification
- **Token Estimate:** 15k reasonable
- **Issue:** Production deployment not explicitly included
- **Fix:** Add Task-0 for production deployment

---

## Dependencies & Phase Ordering ✅

**Phase flow is logical:**
- Phase 0 → Phase 1: Foundation before implementation ✅
- Phase 1 → Phase 2-3: Infrastructure before backend tests ✅
- Phase 1 → Phase 4-5: Infrastructure before frontend tests ✅
- Phase 2-5 → Phase 6: Tests before CI/CD integration ✅

**No circular dependencies detected.**

**Parallelization opportunity:** Phases 2-3 (backend) and 4-5 (frontend) could be done in parallel by different engineers, but plan assumes single engineer (appropriate).

---

## Codebase Alignment ✅

**Backend structure verified:**
- Lambda handler: `backend/lambda_function.py` ✅
- Source code: `backend/src/` (handlers, services, models, config, utils) ✅
- Existing tests: `backend/tests/unit/` (3 test files) ✅
- Test infrastructure: `backend/tests/conftest.py`, `fixtures/`, `mocks/` ✅

**Frontend structure verified:**
- Components: `components/*.tsx` (13+ components) ✅
- Existing tests: `components/__tests__/` (7 test files) ✅
- Plan accounts for untested components (history, AuthScreen, AudioRecording, etc.) ✅

**GitHub Actions:**
- Existing workflows: `backend-tests.yml`, `frontend-tests.yml` ✅
- Plan will add: `deploy-backend-staging.yml` ✅

**Infrastructure:**
- No `infrastructure/` directory yet (to be created in Phase-1, Task-1) ✅

---

## Test Coverage Strategy ✅

**Backend targets are realistic:**
- Lambda handler: 31% → 60%+ (needs ~15 new test cases) ✅
- Services: 59% → 80%+ (needs additional unit + integration tests) ✅
- Middleware: 18% → 60%+ (needs new test file) ✅
- Overall: 39% → 65%+ (achievable with Phases 2-3) ✅

**Frontend targets are realistic:**
- Current: 7 test files covering ~12 components
- Target: All 12+ components with 70%+ coverage ✅
- Integration + E2E tests for critical flows ✅

**Test pyramid alignment (ADR-5):** ✅
- 70% unit tests (Phases 2, 4)
- 20% integration tests (Phases 3, 5)
- 10% E2E tests (Phases 3, 5)

---

## Commit Strategy ✅

**All tasks include commit message templates following Conventional Commits (ADR-8):**
- 51 commit templates across all phases ✅
- Format: `type(scope): description` ✅
- Types: feat, fix, test, refactor, docs, chore, ci, perf ✅
- Scopes: infrastructure, backend, frontend, tests ✅

**Granularity is appropriate:**
- Each task = 1 commit ✅
- Atomic changes ✅
- Clear descriptions ✅

---

## Documentation Completeness ✅

**Plan includes:**
- Architecture Decision Records (8 ADRs in Phase-0) ✅
- Testing strategy (backend + frontend) ✅
- Coding conventions (Python + TypeScript) ✅
- Common pitfalls (backend, frontend, infrastructure) ✅
- Development workflow and TDD flow ✅
- Verification checklists for every task (51 total) ✅
- Testing instructions for every task (51 total) ✅

**Missing:**
- FFmpeg layer setup instructions ❌ (Critical)
- E2E framework decision (Detox) ❌ (Critical)
- Production deployment procedure ⚠️ (Nice to have)

---

## Final Recommendations

### Must Fix Before Implementation (Priority 1)

1. ✅ **Add FFmpeg Layer Setup to Phase-0** (ADR-9)
   - Document build/deploy process
   - Provide public layer alternatives
   - Add troubleshooting guidance

2. ✅ **Make Phase-0 Completion Criteria Objective**
   - Add verification checkpoints
   - Add self-assessment questions
   - Remove subjective criteria

3. ✅ **Add S3 Bucket Naming Guidance** (Phase-1, Task-3)
   - Document global uniqueness requirement
   - Provide naming strategies (account ID suffix)
   - Add troubleshooting for collision errors

4. ✅ **Add E2E Framework Decision to Phase-0** (ADR-10: Detox)
   - Document rationale for choosing Detox
   - List alternatives considered
   - Update Phase-5 to be Detox-specific

5. ✅ **Add Parameter File Security Checkpoint** (Phase-1, Task-6)
   - Require .gitignore verification before creating staging.json
   - Add test procedure for .gitignore
   - Add double-check steps

### Should Fix (Priority 2)

6. ⚠️ **Add Deployment Rollback Guidance** (Phase-1, Task-8)
   - Document common failure scenarios
   - Provide debugging commands
   - Explain rollback behavior

7. ⚠️ **Add Production Deployment Task** (Phase-6, Task-0)
   - Explicit production deployment procedure
   - Change set review requirement
   - Smoke testing steps

8. ⚠️ **Add Token Budget Contingency** (README)
   - Note 175-200k recommended budget
   - Identify which tasks may exceed estimates
   - Provide priority guidance if budget exceeded

9. ⚠️ **Replace Hardcoded Branch Name** (Phase-0)
   - Use `<your-feature-branch>` placeholder

---

## Approval Decision

### Status: ❌ **CONDITIONAL APPROVAL**

**The plan must address all Priority 1 issues before implementation begins.**

**Rationale:**
- Priority 1 issues are **blockers** that will halt implementation
- FFmpeg layer (P1 #1) blocks Phase-1, Task-8
- S3 bucket naming (P1 #3) will cause deployment failures
- E2E framework (P1 #4) will cause significant token budget overrun
- Parameter security (P1 #5) creates security incident risk

**Once Priority 1 issues are fixed:**
- Plan will be **APPROVED** for implementation
- Priority 2 suggestions improve quality but aren't blockers
- Engineer can proceed with confidence

**Estimated Fix Time:** ~2-3 hours to address all Priority 1 issues

---

## Summary

This is a **high-quality, well-structured plan** with:
- ✅ Comprehensive Phase-0 foundation
- ✅ Clear task breakdown with verification
- ✅ Realistic token estimates
- ✅ Proper test coverage strategy
- ✅ Good commit message templates

**However, 5 critical gaps will block implementation:**
1. FFmpeg layer setup not documented
2. Phase-0 completion criteria too subjective
3. S3 bucket naming collision handling missing
4. E2E framework decision deferred to Phase-5
5. Parameter file security risk

**Fix Priority 1 issues, then proceed with confidence.**

---

**Reviewer Signature:** Tech Lead
**Review Complete:** 2025-11-18
