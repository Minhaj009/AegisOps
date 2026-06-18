---
name: test-driven-dev
description: Workflow for validating patches via isolated test suite execution.
when_to_use: Use when running verification sandboxes to execute exploit replications or verify security patches.
---

# Test-Driven Development (TDD) Skill

This skill defines the verification cycle for patches inside AegisOps.

## Verification Cycle

1.  **Red Phase**:
    *   Deploy the vulnerable target codebase inside `/sandbox/Dockerfile`.
    *   Run test cases / exploit scripts that reproduce the security flaw (exits with non-zero code).
2.  **Green Phase**:
    *   Inject the proposed patch from Patch Developer Agent.
    *   Re-run the test suite (exits with zero code).
3.  **Refactor Phase**:
    *   Clean up variable scopes and remove temporary log printouts.
    *   Re-verify test execution.
