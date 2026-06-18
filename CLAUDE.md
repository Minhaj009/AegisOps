# CLAUDE.md - Workspace LLM Profile & Guidelines

This document dictates how Claude models executing inside the AegisOps workspace must interpret coding tasks, write deterministic code, and handle security constraints.

## 1. Absolute Grounding Requirement
> [!IMPORTANT]
> Before writing or modifying any Alibaba Cloud Python SDK code or infrastructure interaction methods, you must mentally trace and match your parameters against the official endpoints specified in Section 9 of the Implementation Plan.
> Official API references:
> * Model Studio: https://www.alibabacloud.com/help/en/model-studio/developer-reference/
> * ECS: https://www.alibabacloud.com/help/en/ecs/developer-reference/
> * ACK/Sandbox: https://www.alibabacloud.com/help/en/ack/developer-reference/
> * OpenAPI Explorer: https://next.api.alibabacloud.com/home

## 2. Coding Standards
*   **Language**: Python 3.10+ with strict typing using `typing` (TypeVar, Union, Optional, Callable, Any).
*   **Dependency Injection**: Initialize gateways, databases, and configuration settings using explicit constructor parameters. Avoid global state or ad-hoc environment checks mid-function.
*   **Return Types**: Every function must declare return types. Return `Optional` or throw specific custom exceptions instead of returning generic `dict` structures or None.
*   **Linting & Testing**: Code must pass `py_compile` checks. Write unit tests following Test-Driven Development (TDD) principles before writing functional logic.

## 3. Error Management & Zero Hallucination
*   **No Schema Guessing**: If you are unsure of a payload argument structure (e.g. for Alibaba Cloud SDK calls or custom MCP inputs), stop and query the local schema config files (`/src/tools/mcp_config.json`) or check the OpenAPI Explorer.
*   **Graceful Recovery**: Implement defensive retry structures using backoff. Never leave a bare `try-except` block; always log exceptions using the unified structured logger (`/src/observability/logger.py`).
