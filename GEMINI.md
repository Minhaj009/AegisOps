# GEMINI.md - Workspace LLM Profile & Guidelines

This document dictates how Gemini models executing inside the AegisOps workspace must interpret coding tasks, handle structured tool calls, and interact with Alibaba Cloud interfaces.

## 1. Absolute Grounding Requirement
> [!IMPORTANT]
> Before writing or modifying any Alibaba Cloud Python SDK code or infrastructure interaction methods, you must mentally trace and match your parameters against the official endpoints specified in Section 9 of the Implementation Plan.
> Official API references:
> * Model Studio: https://www.alibabacloud.com/help/en/model-studio/developer-reference/
> * ECS: https://www.alibabacloud.com/help/en/ecs/developer-reference/
> * ACK/Sandbox: https://www.alibabacloud.com/help/en/ack/developer-reference/
> * OpenAPI Explorer: https://next.api.alibabacloud.com/home

## 2. Structured Outputs & API Schemas
*   **Structured Output Formats**: Prefer returning valid Pydantic models or strictly typed schemas for agent state transfers.
*   **JSON Schema Compliance**: All JSON-based responses must validate against schemas defined in `/src/tools/mcp_config.json` and `/src/orchestrator/rules.json`.
*   **Zero Hallucination**: Do not hallucinate properties, parameter names, or HTTP headers. If an API signature is unknown, consult official documentation links or verify via OpenAPI Explorer.

## 3. Tool Execution & Error Boundaries
*   **Pre-execution Checks**: Intercept all tool calls with `/hooks/pre_tool_call_validator.py` before proposing execution.
*   **Error Logging**: Implement exhaustive exception wrappers. Log structured errors using the metrics tracker (`/src/observability/metrics_tracker.py`) to monitor failure rates and execution cost.
