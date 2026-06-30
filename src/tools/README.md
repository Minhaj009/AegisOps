# AegisOps Custom Model Context Protocol (MCP) Tools

This directory contains the configurations, runtime engine, and specifications for the custom Model Context Protocol (MCP) tools used by the AegisOps.dev remediation pipeline.

## 1. Directory Structure
*   `mcp_config.json`: The static declaration of tools, command arguments, and JSON input schemas.
*   `mcp_server.py`: The executable Python process implementing the FastMCP server.

---

## 2. Tool Reference & Routing Guidelines

### `get_repository_tree`
*   **Purpose**: Recursively walks the repository, ignores files matching `.gitignore` patterns, and returns a lightweight structural hierarchical tree representation. It prunes empty subtrees that do not contain targeted extensions.
*   **Target Extensions**: `.py`, `.js`, `.cpp`, `.txt`
*   **Input Schema**:
    *   `target_path` (string, mandatory): Absolute path to the repository directory to inspect.
*   **Output Contract**:
    *   Returns a plain text ASCII-style tree layout of directories and files.
*   **Error Boundaries**:
    *   If the target directory does not exist or is inaccessible, returns a descriptive error message starting with `Error:`.

### `view_file_content`
*   **Purpose**: Safely reads the contents of a single file. Supports optional line-range slicing to return only the requested chunk, preventing context window bloat.
*   **Input Schema**:
    *   `file_path` (string, mandatory): Absolute path to the target file.
    *   `start_line` (integer, optional): Start line number (1-indexed, inclusive) to begin slicing.
    *   `end_line` (integer, optional): End line number (1-indexed, inclusive) to end slicing.
*   **Output Contract**:
    *   Returns a plain text containing a header specifying the sliced lines, followed by the raw text contents of the sliced file segment.
*   **Error Boundaries**:
    *   If the target file does not exist, is not a file, or if `start_line` exceeds `end_line`, returns an error string starting with `Error:`.

### `flag_dependency_drift`
*   **Purpose**: Reads the target manifest file (such as `requirements.txt`), extracts package names and version constraints, and formats them as a clean list for auditing.
*   **Input Schema**:
    *   `manifest_path` (string, mandatory): Absolute path to the dependency manifest file.
*   **Output Contract**:
    *   Returns a plain text block containing a header followed by a list of parsed package dependencies and their operator/version constraints.
*   **Error Boundaries**:
    *   If the manifest file does not exist or is not a file, returns a descriptive error message starting with `Error:`.

---

## 3. Invocation & Execution Guidelines

### Execution command
To run the MCP server locally over the stdio transport:
```bash
python -m src.tools.mcp_server
```

### JSON RPC Integration
*   Ensure all keys and values in payloads utilize double quotes (`"`).
*   Validate payload structures against the declared JSON Schema in `/src/tools/mcp_config.json`.
