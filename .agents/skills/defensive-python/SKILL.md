---
name: defensive-python
description: Strict defensive coding rules to prevent syntax errors, type drift, and security regressions.
when_to_use: Use when writing or modifying any Python runtime scripts or sub-agent logic.
---

# Defensive Python Skill

This skill enforces high code quality, security correctness, and strict typing across our Python codebase.

## Core Rules

1.  **Strict Typing**:
    *   Utilize type hints for all parameters and function return values.
    *   Avoid returning generic `Any` types; specify exact structures or custom models where possible.
2.  **Explicit Scopes**:
    *   Do not write global variables. Pass settings and database instances explicitly to class constructors.
3.  **Command Execution Protection**:
    *   Never call `os.system` or pass raw unvalidated shell strings to `subprocess.Popen`.
    *   Always use list parameters (`subprocess.run(["cmd", "arg1", "arg2"])`) to prevent shell injection vulnerabilities.
4.  **Error Isolation**:
    *   Avoid bare `except:` statements. Specify exact exceptions (`KeyError`, `ValueError`, `dashscope.api_entities.exceptions.APIError`).
    *   Log all caught errors through the unified JSON logger (`/src/observability/logger.py`).
