# -*- coding: utf-8 -*-
"""
AegisOps Pre-Tool Call Validator Hook
=====================================
Intercepts and validates command arguments or tool call payloads 
before execution, checking for forbidden syntax and destructive patterns.
"""

import sys
import re
import json
from typing import Dict, Any, List

# List of regex rules indicating forbidden operations
FORBIDDEN_COMMAND_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-f\s+.*passwd",
    r"dd\s+if=",
    r"chmod\s+-R\s+777",
    r"chown\s+-R\s+.*",
    r"mkfs",
    r"git\s+push\s+.*--force",
    r"shred\s+"
]

class PreToolCallValidator:
    """Validator designed to intercept tool commands and prevent agentic command escapades."""

    def __init__(self):
        self.compiled_rules = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_COMMAND_PATTERNS]

    def validate_command(self, cmd: str) -> bool:
        """Scan a command string for dangerous signatures."""
        for rule in self.compiled_rules:
            if rule.search(cmd):
                return False
        return True

    def validate_payload(self, tool_name: str, payload: Dict[str, Any]) -> bool:
        """Scan structured payload contents for command injection risks."""
        # Convert payload to string representation to scan for patterns
        serialized = json.dumps(payload)
        for rule in self.compiled_rules:
            if rule.search(serialized):
                return False
        return True

if __name__ == "__main__":
    validator = PreToolCallValidator()
    
    # CLI check utility
    if len(sys.argv) > 1:
        command_arg = " ".join(sys.argv[1:])
        if not validator.validate_command(command_arg):
            print(f"[AegisOps Guardrail] BLOCKED: Command violates safety rules.")
            sys.exit(1)
        else:
            print("[AegisOps Guardrail] ALLOWED: Command passed validation.")
            sys.exit(0)
    else:
        # Default dry-run test
        print("Running security validator unit tests...")
        test_good = "git status"
        test_bad = "rm -rf / --no-preserve-root"
        assert validator.validate_command(test_good) == True
        assert validator.validate_command(test_bad) == False
        print("All guardrail dry-runs passed successfully.")
        sys.exit(0)
