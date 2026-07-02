# -*- coding: utf-8 -*-
"""
AegisOps Patch Applier Engine
=============================
Parses LLM-generated Search-and-Replace patches and applies them to the workspace.
"""

import os
import re
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("AegisOps.PatchApplier")

class PatchApplier:
    """Parses and applies search-and-replace patches to source files."""

    @staticmethod
    def parse_patch(patch_content: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """
        Parses patch content containing file blocks and search-replace chunks.
        
        Example format:
        FILE: path/to/file.py
        <<<<<<< SEARCH
        old code
        =======
        new code
        >>>>>>> REPLACE
        """
        # Split by file markers
        file_sections = re.split(r"^FILE:\s*([^\n\r]+)", patch_content, flags=re.MULTILINE)
        
        results = []
        if len(file_sections) < 3:
            # Fallback: Check if there's just search-replace blocks without a file header,
            # we'll return them with an empty filename and let the router map it to a default.
            chunks = PatchApplier._parse_chunks(patch_content)
            if chunks:
                results.append(("", chunks))
            return results

        # Process pairs of (filename, content)
        for i in range(1, len(file_sections), 2):
            filename = file_sections[i].strip()
            content = file_sections[i+1]
            chunks = PatchApplier._parse_chunks(content)
            if chunks:
                results.append((filename, chunks))
                
        return results

    @staticmethod
    def _parse_chunks(content: str) -> List[Tuple[str, str]]:
        """Extract search-replace blocks from a section of text."""
        pattern = re.compile(
            r"<<<<<<< SEARCH[\r\n]+(.*?)(?=[\r\n]+=======)[\r\n]+=======[\r\n]+(.*?)(?=[\r\n]+>>>>>>> REPLACE)[\r\n]+>>>>>>> REPLACE",
            re.DOTALL
        )
        matches = pattern.findall(content)
        return [(m[0], m[1]) for m in matches]

    def apply_patch(self, target_base_path: str, patch_content: str, default_file: Optional[str] = None) -> List[str]:
        """
        Applies parsed search-and-replace chunks to files under the target base path.
        
        Returns:
            List of modified file paths (absolute).
        """
        parsed_files = self.parse_patch(patch_content)
        if not parsed_files:
            raise ValueError("No valid Search-and-Replace patches found in agent output.")

        modified_files = []

        for filename, chunks in parsed_files:
            # Resolve target file path
            file_to_patch = filename or default_file
            if not file_to_patch:
                raise ValueError("Could not determine target file path for patch chunk.")

            abs_file_path = os.path.abspath(os.path.join(target_base_path, file_to_patch))
            if not abs_file_path.startswith(os.path.abspath(target_base_path)):
                raise ValueError(f"Path traversal detected! Target path '{abs_file_path}' is outside base path.")

            if not os.path.exists(abs_file_path):
                raise FileNotFoundError(f"Target file for patch does not exist: {file_to_patch}")

            # Apply replacements
            logger.info(f"Applying {len(chunks)} patches to {file_to_patch}")
            with open(abs_file_path, "r", encoding="utf-8", errors="replace") as f:
                file_text = f.read()

            for search_block, replace_block in chunks:
                # 1. Normalize line endings to \n for both file and search/replace blocks
                normalized_file = file_text.replace("\r\n", "\n").replace("\r", "\n")
                normalized_search = search_block.replace("\r\n", "\n").replace("\r", "\n")
                normalized_replace = replace_block.replace("\r\n", "\n").replace("\r", "\n")
                
                # Check exact normalized match first
                exact_index = normalized_file.find(normalized_search)
                if exact_index != -1:
                    file_text = normalized_file.replace(normalized_search, normalized_replace, 1)
                else:
                    # 2. Fuzzy spacing matching (for split lines, indentation, spacing variations)
                    # Split search block into word tokens, whitespace tokens, and individual punctuation tokens
                    tokens = re.split(r"(\s+|[a-zA-Z0-9_]+)", normalized_search)
                    regex_parts = []
                    last_was_space = False
                    
                    for token in tokens:
                        if not token:
                            continue
                        if token.isspace():
                            regex_parts.append(r"\s+")
                            last_was_space = True
                        else:
                            if regex_parts and not last_was_space:
                                regex_parts.append(r"\s*")
                            regex_parts.append(re.escape(token))
                            last_was_space = False
                            
                    pattern_str = r"\s*" + "".join(regex_parts) + r"\s*"
                    
                    try:
                        pattern = re.compile(pattern_str, re.DOTALL)
                        matches = list(pattern.finditer(normalized_file))
                        
                        if not matches:
                            snippet = search_block[:100] + "..." if len(search_block) > 100 else search_block
                            raise LookupError(
                                f"Search block not found in file '{file_to_patch}' (even after fuzzy matching):\n{snippet}"
                            )
                        
                        # Apply to the first match
                        m = matches[0]
                        normalized_file = normalized_file[:m.start()] + normalized_replace + normalized_file[m.end():]
                        file_text = normalized_file
                        
                    except re.error as re_err:
                        logger.error(f"Fuzzy regex compilation failed for search block: {re_err}")
                        snippet = search_block[:100] + "..." if len(search_block) > 100 else search_block
                        raise LookupError(f"Search block not found in file '{file_to_patch}':\n{snippet}")

            # Write back modified code
            with open(abs_file_path, "w", encoding="utf-8") as f:
                f.write(file_text)

            modified_files.append(abs_file_path)

        return modified_files
