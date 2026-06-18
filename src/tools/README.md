# AegisOps Custom Model Context Protocol (MCP) Tools

This directory contains the configurations, runtime engine, and specifications for custom Model Context Protocol (MCP) servers used by the AegisOps.dev remediation pipeline.

## 1. Directory Structure
*   `mcp_config.json`: The static declaration of tools, command arguments, and JSON input schemas.
*   `mcp_server.py`: The executable python process implementing stdin/stdout JSON-RPC messaging.

---

## 2. Invocations & Routing Guidelines

### When to Invoke
1.  **Repository Parsing (`repo-parser:parse_codebase_ast`)**:
    *   Invoke immediately after agent initialization to map out file trees, class hierarchies, and function dependencies.
2.  **Vulnerability Scanning (`vuln-scanner:scan_vulnerabilities`)**:
    *   Invoke during threat analysis phases to locate static code flaws, CVE exposures, or deployment misconfigurations.
3.  **Environment Provisioning (`env-provisioner:provision_sandbox_container`)**:
    *   Invoke prior to executing test reproduction scripts or verifying patch remediations.

### Strict Argument Validation
> [!IMPORTANT]
> All custom MCP servers initiating operations against Alibaba Cloud infrastructure (e.g. provisioning ECS instances or ACK resources) MUST validate payload arguments against schemas defined in the official Alibaba Cloud OpenAPI Explorer:
> **Reference Portal**: `https://next.api.alibabacloud.com/home`
> 
> Failing to align parameter names, types, or nesting with the official OpenAPI spec will result in immediate execution failure.

---

## 3. Formatting JSON Payload Arguments
To eliminate JSON parse errors:
*   Ensure all keys and values in payloads utilize double quotes (`"`).
*   Escape inner quotes inside parameter strings appropriately.
*   Validate payload structures against the declared JSON Schema in `/src/tools/mcp_config.json`.
*   Example payload:
    ```json
    {
      "jsonrpc": "2.0",
      "method": "provision_sandbox_container",
      "params": {
        "sandbox_id": "sb_98237482_ae",
        "image_name": "aegisops-sandbox:latest",
        "cpu_limit": "2.0",
        "mem_limit": "1024m"
      },
      "id": 1
    }
    ```
