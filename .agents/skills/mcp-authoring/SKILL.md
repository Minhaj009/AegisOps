---
name: mcp-authoring
description: Guidelines and patterns for creating and deploying custom Model Context Protocol (MCP) servers.
when_to_use: Use when adding new capability tools, parsing formats, or provisioning sandboxes via custom JSON-RPC engines.
---

# MCP Authoring Skill

This skill anchors guidelines for constructing custom Model Context Protocol (MCP) server engines.

## Core Directives

1.  **Strict Schema Declarations**:
    *   Define all tool arguments inside `/src/tools/mcp_config.json`.
    *   Declare validation constraints (types, patterns, enum restrictions).
2.  **JSON-RPC Stdin/Stdout Wrapper**:
    *   Extend `/src/tools/mcp_server.py` to route calls to target actions.
    *   Capture exceptions and wrap them inside standard JSON-RPC error responses.
3.  **Grounding Validation**:
    *   Before implementing new infrastructure actions, match parameter schemas against the official Alibaba Cloud OpenAPI Explorer endpoint structure.
