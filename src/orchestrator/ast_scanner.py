# -*- coding: utf-8 -*-
"""
AegisOps AST Static Vulnerability Scanner
=========================================
Parses Python source files into Abstract Syntax Trees (ASTs) to flag security
flaws (CWE-78, CWE-89, CWE-94, CWE-502, CWE-798) programmatically.
"""

import os
import ast
import logging
from typing import List, Dict, Any

logger = logging.getLogger("AegisOps.ASTScanner")

class AegisASTVisitor(ast.NodeVisitor):
    """AST visitor to inspect nodes for common security vulnerabilities."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Dict[str, Any]] = []
        self.lines: List[str] = []

    def get_source_line(self, lineno: int) -> str:
        """Retrieves a single line of source code based on 1-indexed line number."""
        if 0 < lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def visit_Call(self, node: ast.Call):
        """Inspect function calls for dangerous operations."""
        func_name = ""
        # Handle simple name calls: eval(x)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        # Handle attribute calls: subprocess.run(x)
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            # Reconstruct module name if possible
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"

        # 1. CWE-94: Code Execution (eval, exec)
        if func_name in ("eval", "exec"):
            self.findings.append({
                "file": self.filename,
                "line": node.lineno,
                "cwe": "CWE-94",
                "vulnerability": "Insecure Code Execution (eval/exec)",
                "severity": "CRITICAL",
                "code": self.get_source_line(node.lineno),
                "description": f"Use of dangerous built-in '{func_name}' permits arbitrary code execution."
            })

        # 2. CWE-78: OS Command Injection (subprocess with shell=True, os.system, os.popen)
        elif func_name in ("os.system", "os.popen", "system", "popen"):
            self.findings.append({
                "file": self.filename,
                "line": node.lineno,
                "cwe": "CWE-78",
                "vulnerability": "OS Command Injection",
                "severity": "CRITICAL",
                "code": self.get_source_line(node.lineno),
                "description": f"Dangerous function call '{func_name}' executes string commands directly in shell."
            })
            
        elif func_name in ("subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call", "subprocess.check_output"):
            # Check keywords for shell=True
            shell_true = False
            for kw in node.keywords:
                if kw.arg == "shell":
                    # Check if value is constant True
                    if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        shell_true = True
                    # Legacy support for older AST versions
                    elif isinstance(kw.value, ast.Name) and kw.value.id == "True":
                        shell_true = True

            if shell_true:
                self.findings.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "cwe": "CWE-78",
                    "vulnerability": "OS Command Injection (shell=True)",
                    "severity": "HIGH",
                    "code": self.get_source_line(node.lineno),
                    "description": f"Use of '{func_name}' with shell=True bypasses argument escaping and can lead to command injection."
                })

        # 3. CWE-502: Insecure Deserialization (pickle, yaml.unsafe_load)
        elif func_name in ("pickle.load", "pickle.loads", "pickle.Unpickler"):
            self.findings.append({
                "file": self.filename,
                "line": node.lineno,
                "cwe": "CWE-502",
                "vulnerability": "Insecure Deserialization (Pickle)",
                "severity": "CRITICAL",
                "code": self.get_source_line(node.lineno),
                "description": "Deserialization of untrusted pickle data allows execution of arbitrary object constructors."
            })
        elif func_name in ("yaml.unsafe_load", "yaml.load"):
            # Check if Loader keyword is safe
            loader_safe = False
            for kw in node.keywords:
                if kw.arg == "Loader":
                    if isinstance(kw.value, ast.Attribute) and kw.value.attr in ("SafeLoader", "CSafeLoader"):
                        loader_safe = True
            
            if func_name == "yaml.unsafe_load" or not loader_safe:
                self.findings.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "cwe": "CWE-502",
                    "vulnerability": "Insecure Deserialization (PyYAML)",
                    "severity": "HIGH",
                    "code": self.get_source_line(node.lineno),
                    "description": f"Use of unsafe loader in '{func_name}' can execute arbitrary code inside YAML streams."
                })

        # 4. CWE-89: SQL Injection (Raw cursor execute with formatted strings)
        elif func_name in ("cursor.execute", "execute"):
            # Check first argument for string interpolation
            if node.args:
                first_arg = node.args[0]
                is_insecure = False
                
                # Check for f-string: cursor.execute(f"...")
                if isinstance(first_arg, ast.JoinedStr):
                    is_insecure = True
                # Check for string %: cursor.execute("..." % var)
                elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod):
                    is_insecure = True
                # Check for string format: cursor.execute("...".format(var))
                elif isinstance(first_arg, ast.Call) and isinstance(first_arg.func, ast.Attribute) and first_arg.func.attr == "format":
                    is_insecure = True

                if is_insecure:
                    # Double check if SQL-like keywords exist in the string to prevent false positives
                    source_str = self.get_source_line(node.lineno).lower()
                    sql_keywords = ("select", "insert", "update", "delete", "where", "from", "join")
                    if any(kw in source_str for kw in sql_keywords):
                        self.findings.append({
                            "file": self.filename,
                            "line": node.lineno,
                            "cwe": "CWE-89",
                            "vulnerability": "SQL Injection Flaw",
                            "severity": "HIGH",
                            "code": self.get_source_line(node.lineno),
                            "description": "SQL statement constructed using variable formatting instead of parameterized inputs."
                        })

        # Continue traversing children
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Check assignment statements for hardcoded credentials (CWE-798)."""
        # Targets represent the variable names
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.upper()
                # Flag keywords related to secrets
                cred_keywords = ("API_KEY", "SECRET", "SECRET_KEY", "PASSWORD", "PASSWD", "AUTH_TOKEN")
                if any(kw in var_name for kw in cred_keywords):
                    # Check if the assigned value is a string literal
                    is_secret_literal = False
                    val_len = 0
                    
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        is_secret_literal = True
                        val_len = len(node.value.value)
                    # Legacy support for older python versions
                    elif isinstance(node.value, ast.Str):
                        is_secret_literal = True
                        val_len = len(node.value.s)

                    # Exclude empty placeholders or env fetches
                    if is_secret_literal and val_len > 8:
                        # Exclude placeholders
                        source_line = self.get_source_line(node.lineno).lower()
                        placeholders = ("placeholder", "your_", "key_here", "example", "env.get", "environ")
                        if not any(pl in source_line for pl in placeholders):
                            self.findings.append({
                                "file": self.filename,
                                "line": node.lineno,
                                "cwe": "CWE-798",
                                "vulnerability": "Hardcoded Credentials",
                                "severity": "HIGH",
                                "code": self.get_source_line(node.lineno),
                                "description": f"Variable '{target.id}' assigned a hardcoded secret literal of length {val_len}."
                            })

        self.generic_visit(node)


class ASTScanner:
    """Orchestrates static analysis scanning over target directories."""

    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(base_path)

    def scan(self) -> List[Dict[str, Any]]:
        """Walks directory, parses python files, and runs visitor checks."""
        all_findings = []
        
        if not os.path.exists(self.base_path):
            logger.warning(f"Scan path {self.base_path} does not exist.")
            return all_findings

        # If target path is a single file
        if os.path.isfile(self.base_path):
            if self.base_path.endswith(".py"):
                all_findings.extend(self._scan_file(self.base_path))
            return all_findings

        # Traverse directory
        for root, _, files in os.walk(self.base_path):
            # Skip ignored directories like .git or sandbox/env directories
            if any(dir_name in root for dir_name in (".git", ".agents", "venv", "__pycache__")):
                continue
                
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    all_findings.extend(self._scan_file(full_path))

        return all_findings

    def _scan_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Parses a single file and returns its findings."""
        findings = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
                f.seek(0)
                lines = f.readlines()
                
            tree = ast.parse(source, filename=filepath)
            
            # Use relative path for visual clarity in findings report
            rel_path = os.path.relpath(filepath, self.base_path)
            
            visitor = AegisASTVisitor(rel_path)
            visitor.lines = lines
            visitor.visit(tree)
            findings = visitor.findings
            
        except SyntaxError as se:
            logger.warning(f"AST Parsing failed for {filepath}: SyntaxError at line {se.lineno}")
        except Exception as e:
            logger.warning(f"Failed to scan file {filepath}: {str(e)}")
            
        return findings

    def generate_markdown_report(self) -> str:
        """Runs scan and formats results into a markdown footprint report."""
        findings = self.scan()
        if not findings:
            return "Lead Auditor AST Scan: No vulnerabilities detected in code files."
            
        report = "### Lead Auditor AST Scan Report\n"
        report += f"Detected **{len(findings)}** security vulnerabilities:\n\n"
        
        for idx, f in enumerate(findings, 1):
            report += f"{idx}. **[{f['severity']}] {f['vulnerability']} ({f['cwe']})**\n"
            report += f"   - **Location**: `{f['file']}` (Line {f['line']})\n"
            report += f"   - **Snippet**: `{f['code']}`\n"
            report += f"   - **Description**: {f['description']}\n\n"
            
        return report


if __name__ == "__main__":
    # Test execution
    scanner = ASTScanner("demo_targets/vulnerable_app")
    print(scanner.generate_markdown_report())
