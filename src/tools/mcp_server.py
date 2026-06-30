# -*- coding: utf-8 -*-
"""
AegisOps MCP Server Engine
=========================
Custom Model Context Protocol (MCP) server providing repository walking, 
file viewing, and dependency auditing tools.
"""

import sys
import os
import re
import logging
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

# Configure logging to sys.stderr to avoid corrupting stdio transport JSON-RPC channels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("AegisOps.MCPServer")

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logger.error("Failed to import mcp SDK. Ensure 'mcp' is installed via requirements.txt.")
    sys.exit(1)

# Initialize the FastMCP server
mcp = FastMCP("AegisOps Tools")

def parse_gitignore(repo_path: Path) -> List[str]:
    """Parse .gitignore file at repository root and return pattern list."""
    gitignore_path = repo_path / ".gitignore"
    patterns = []
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception as e:
            logger.error(f"Error reading .gitignore: {str(e)}")
    
    # Always ignore common system, version control, caches, and local configurations
    patterns.extend([".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".agents", ".githooks", "hooks"])
    return patterns

def is_ignored(path: Path, repo_path: Path, patterns: List[str]) -> bool:
    """Check if the given path should be filtered out based on gitignore patterns."""
    try:
        rel_path = path.relative_to(repo_path)
    except ValueError:
        return False
        
    rel_path_str = rel_path.as_posix()
    
    for pattern in patterns:
        pat = pattern.rstrip('/')
        
        # Check directory-specific matching (ends with slash)
        if pattern.endswith('/'):
            if any(fnmatch.fnmatch(part, pat) for part in rel_path.parts):
                return True
        else:
            # File or general wildcard match
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
            # Segment match
            if any(fnmatch.fnmatch(part, pat) for part in rel_path.parts):
                return True
    return False

def has_matching_files(dir_path: Path, repo_path: Path, gitignore_patterns: List[str], target_extensions: Set[str]) -> bool:
    """Helper to check if a directory recursively contains any valid code/text files (pruning empty subtrees)."""
    try:
        for entry in dir_path.iterdir():
            if is_ignored(entry, repo_path, gitignore_patterns):
                continue
            if entry.is_dir():
                if has_matching_files(entry, repo_path, gitignore_patterns, target_extensions):
                    return True
            elif entry.suffix in target_extensions:
                return True
    except Exception:
        pass
    return False

def generate_tree(repo_path: Path, current_path: Path, gitignore_patterns: List[str], target_extensions: Set[str], prefix: str = "") -> List[str]:
    """Recursively generate an ASCII representation of the filtered workspace directory hierarchy."""
    lines = []
    try:
        entries = sorted(list(current_path.iterdir()), key=lambda e: (not e.is_dir(), e.name.lower()))
    except Exception as e:
        logger.error(f"Cannot read directory {current_path}: {str(e)}")
        return [f"{prefix}[ERROR: Access Denied]"]

    # Filter out ignored paths and empty folders
    filtered_entries = []
    for entry in entries:
        if is_ignored(entry, repo_path, gitignore_patterns):
            continue
        if entry.is_dir():
            if has_matching_files(entry, repo_path, gitignore_patterns, target_extensions):
                filtered_entries.append(entry)
        elif entry.suffix in target_extensions:
            filtered_entries.append(entry)

    # Format the tree branches
    for i, entry in enumerate(filtered_entries):
        is_last = (i == len(filtered_entries) - 1)
        connector = "`-- " if is_last else "|-- "
        
        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            new_prefix = prefix + ("    " if is_last else "|   ")
            lines.extend(generate_tree(repo_path, entry, gitignore_patterns, target_extensions, new_prefix))
        else:
            lines.append(f"{prefix}{connector}{entry.name}")
    return lines

@mcp.tool()
def get_repository_tree(target_path: str) -> str:
    """
    Recursively walk the repository, filtering for files matching targeted extensions (.py, .js, .cpp, .txt). 
    Obeys .gitignore rules and returns a lightweight structural tree hierarchy representation.
    """
    try:
        path = Path(target_path).resolve()
        if not path.exists():
            return f"Error: Target path '{target_path}' does not exist."
        if not path.is_dir():
            return f"Error: Target path '{target_path}' is not a directory."

        patterns = parse_gitignore(path)
        target_exts = {".py", ".js", ".cpp", ".txt"}
        
        tree_lines = [f"{path.name}/"]
        tree_lines.extend(generate_tree(path, path, patterns, target_exts))
        return "\n".join(tree_lines)
    except Exception as e:
        logger.error(f"Failed to generate repository tree: {str(e)}")
        return f"Error: Failure during repository inspection: {str(e)}"

@mcp.tool()
def view_file_content(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """
    Safely read a single targeted file path, with support for optional line-range slicing (1-indexed, inclusive) 
    to return only the requested block.
    """
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if not path.is_file():
            return f"Error: Path '{file_path}' is not a file."

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        s_line = start_line if start_line is not None else 1
        e_line = end_line if end_line is not None else total_lines

        # Clamp range values defensively
        if s_line < 1:
            s_line = 1
        if e_line > total_lines:
            e_line = total_lines
        if s_line > e_line:
            return f"Error: start_line ({s_line}) cannot exceed end_line ({e_line}). Total lines: {total_lines}."

        sliced_content = "".join(lines[s_line - 1:e_line])
        header = f"=== File: {path.name} (Lines {s_line} to {e_line} of {total_lines}) ===\n"
        return header + sliced_content
    except Exception as e:
        logger.error(f"Failed to read file '{file_path}': {str(e)}")
        return f"Error: Failure reading file: {str(e)}"

@mcp.tool()
def flag_dependency_drift(manifest_path: str) -> str:
    """
    Read the target manifest file (requirements.txt), extract version strings, and format them for agent auditing.
    """
    try:
        path = Path(manifest_path).resolve()
        if not path.exists():
            return f"Error: Manifest path '{manifest_path}' does not exist."
        if not path.is_file():
            return f"Error: Manifest path '{manifest_path}' is not a file."

        dependencies = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                
                # Match package, operator, and version (e.g. dashscope>=2.20.0)
                match = re.match(r"^([a-zA-Z0-9_\-\[\]]+)\s*(==|>=|<=|>|<|~=)\s*([a-zA-Z0-9\.\-\*a-fA-F\+]+)", line)
                if match:
                    pkg, op, ver = match.groups()
                    dependencies.append(f"- {pkg}: {op}{ver}")
                else:
                    dependencies.append(f"- {line} (unparsed constraint)")

        header = f"=== Dependency Audit: {path.name} ===\n"
        if not dependencies:
            return header + "No dependency specifications parsed."
        return header + "\n".join(dependencies)
    except Exception as e:
        logger.error(f"Failed to parse dependency manifest: {str(e)}")
        return f"Error: Dependency audit failure: {str(e)}"

if __name__ == "__main__":
    # If run in interactive terminal, show a helper message
    if sys.stdin.isatty():
        print("[AegisOps MCP Tools] Ready. Run via MCP client transport to execute JSON-RPC sessions.")
    else:
        mcp.run()
