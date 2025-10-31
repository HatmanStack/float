# Float App Refactoring - Implementation Plan

## Overview

This plan guides the systematic modernization of the Float meditation app's development infrastructure. The refactoring improves code quality, testing, type safety, and developer experience while preserving the existing Expo/React Native architecture and AWS Lambda backend.

**Status**: In planning phase
**Target Completion**: 6 phases (~3-4 weeks depending on team size)
**Effort**: ~600-800 development hours (distributed across phases)

---

## Key Principles

This refactoring follows these core principles:

- **DRY (Don't Repeat Yourself)**: Eliminate code duplication, centralize configuration
- **YAGNI (You Aren't Gonna Need It)**: Only implement what's needed now; avoid over-engineering
- **TDD (Test-Driven Development)**: Write tests before/alongside code for critical paths
- **Balanced Standards**: Strict enough for quality, lenient enough for pragmatism
- **Incremental Improvement**: Code improves continuously as we refactor

---

## Phase Overview

| Phase | Title | Focus | Est. Duration | Status |
|-------|-------|-------|----------------|--------|
| 0 | Setup & Prerequisites | Architecture decisions, tooling setup | 1-2 days | [📄 View](./Phase-0.md) |
| 1 | Backend Infrastructure | pyproject.toml, requirements, test structure | 3-4 days | [📄 View](./Phase-1.md) |
| 1.5 | Frontend Testing (Optional) | Write Jest tests for components | 2-3 days | [📄 View](./Phase-1.5.md) |
| 2 | Backend Code Quality | Type hints, ruff, black, mypy integration | 4-5 days | [📄 View](./Phase-2.md) |
| 3 | Frontend Tooling | ESLint, Prettier, TypeScript config | 2-3 days | [📄 View](./Phase-3.md) |
| 4 | CI/CD Pipeline | GitHub Actions workflows, automation | 2-3 days | [📄 View](./Phase-4.md) |
| 5 | Documentation | README, CONTRIBUTING, dev guides | 1-2 days | [📄 View](./Phase-5.md) |

---

## Phase Dependencies

```
Phase 0 (Setup & Prerequisites)
    ↓
Phase 1 (Backend Infrastructure)
    ↓
Phase 2 (Backend Code Quality)
    ↓
Phase 3 (Frontend Tooling)
    ↓
Phase 4 (CI/CD Pipeline)
    ↓
Phase 5 (Documentation)
```

Each phase **must complete before the next phase begins**. However, within a phase, tasks can be parallelized where dependencies allow.

---

## Quick Links

- **[Phase 0: Setup & Prerequisites](./Phase-0.md)** - Start here
- **[Phase 1: Backend Infrastructure](./Phase-1.md)**
- **[Phase 1.5: Frontend Testing](./Phase-1.5.md)** - Optional
- **[Phase 2: Backend Code Quality](./Phase-2.md)**
- **[Phase 3: Frontend Tooling](./Phase-3.md)**
- **[Phase 4: CI/CD Pipeline](./Phase-4.md)**
- **[Phase 5: Documentation](./Phase-5.md)**

## Supporting Documents (Plan Revisions)

- **[Feedback Revisions](./FEEDBACK_REVISIONS.md)** - Addresses plan review feedback
- **[Migration Path](../MIGRATION_PATH.md)** - How team transitions to new standards
- **[CI/CD Operations](../CI_CD_OPERATIONS.md)** - What to do when CI fails

---

## Prerequisites (Before Starting)

Before beginning Phase 0, ensure:

1. **Access & Permissions**
   - Git repository access with push/pull permissions
   - GitHub Actions enabled on repository
   - AWS credentials configured (for backend testing)
   - API keys available (Google Gemini, ElevenLabs, OpenAI)

2. **Local Environment**
   - Node.js 18+ installed (via nvm or package manager)
   - Python 3.12+ installed (via pyenv, conda, or package manager)
   - pip and venv tools available
   - Git configured with correct credentials

3. **Knowledge Assumptions**
   - Familiar with React/React Native basics
   - Comfortable with Python and pip package management
   - Basic understanding of pytest testing framework
   - Familiarity with Git workflow and commits

---

## How to Use This Plan

1. **Start with Phase 0** - Read architecture decisions and prerequisites
2. **Follow phases sequentially** - Each builds on the previous
3. **Complete all tasks in a phase** before moving to the next
4. **Commit frequently** - Use provided commit message templates
5. **Verify with checklists** - Ensure each task meets verification criteria

### For Each Task

```
1. Read the task goal and understand what you're building
2. Review files to modify/create
3. Check prerequisites (have all dependencies installed?)
4. Follow step-by-step instructions (they guide but don't specify exact commands)
5. Run verification checklist
6. Write and run tests
7. Commit with provided message template
```

---

## Verification Strategy

Each phase includes:

- **Step-by-step instructions** for implementation
- **Verification checklist** to confirm completion
- **Testing instructions** for automated/manual tests
- **Commit templates** following conventional commits

Commit frequently with atomic changes. Use the provided templates to ensure consistent, clear commit history.

---

## Rollback Strategy

If issues arise:

1. **Within a phase**: Revert to last successful commit and adjust approach
2. **Between phases**: Previous phase can be abandoned without blocking earlier phases
3. **Critical issues**: Document issue and continue with workarounds

Each phase builds on previous work but can be adjusted if needed.

---

## Success Metrics

By the end of all phases:

- ✅ Backend: 100% type hints on public APIs, mypy passing
- ✅ Backend: 60%+ test coverage (critical paths)
- ✅ Frontend: ESLint + Prettier integrated and passing
- ✅ CI/CD: GitHub Actions running tests automatically
- ✅ Development: Clear onboarding docs and contribution guides
- ✅ Code Quality: Consistent formatting, linting, type safety across codebase

---

## Token Budget (Context Window Estimation)

Each phase is sized to fit within a single context window (~100,000 tokens):

- **Phase 0**: ~8,000 tokens (setup + ADRs)
- **Phase 1**: ~18,000 tokens (infrastructure setup)
- **Phase 2**: ~20,000 tokens (code quality + existing code refactoring)
- **Phase 3**: ~15,000 tokens (frontend tooling)
- **Phase 4**: ~12,000 tokens (CI/CD)
- **Phase 5**: ~10,000 tokens (documentation)

**Total**: ~83,000 tokens across all phases

---

## Getting Help

- **Phase documentation**: Each phase has detailed instructions
- **Verification checklists**: Confirm your work at each step
- **Commit templates**: Clear, atomic changes with good messages
- **Code examples**: Patterns provided for tests, type hints, etc.

If blocked:
1. Review the phase documentation
2. Check verification checklist for clues
3. Examine existing code for patterns
4. Refer to tool documentation (pytest, mypy, ruff, etc.)

---

## Notes

- **Don't commit `docs/plans/`** - These are implementation guides, not part of the codebase
- **Use provided commit templates** - Ensures consistent history
- **Run verification after each task** - Catches issues early
- **Ask questions before proceeding** - Better to clarify than guess

---

**Ready to begin? Start with [Phase 0: Setup & Prerequisites](./Phase-0.md)**
