# -*- coding: utf-8 -*-
"""
AegisOps Qwen LLM Gateway
=========================
API Grounding:
* Core Inference (Model Studio / Qwen Engine API): https://www.alibabacloud.com/help/en/model-studio/developer-reference/
"""

import os
import time
import logging
from typing import Dict, Any, Generator, Optional

# Stub importing DashScope/Bailian. In actual runtime: import dashscope
try:
    import dashscope
except ImportError:
    dashscope = None

logger = logging.getLogger("AegisOps.QwenGateway")

class QwenGateway:
    """Core interface wrapper for Alibaba Cloud Model Studio (Qwen-Max/Qwen-Plus)."""

    def __init__(self, api_key: Optional[str] = None):
        # API key priority: argument -> env var
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY environment variable is not set. Requests may fail.")
        else:
            if dashscope:
                dashscope.api_key = self.api_key

        # Standard model settings
        self.default_model = "qwen-max"
        self.max_retries = 3
        self.retry_backoff = 2.0

    def generate_chat(self, 
                      system_prompt: str, 
                      user_prompt: str, 
                      model_name: Optional[str] = None, 
                      temperature: float = 0.2, 
                      stream: bool = False) -> Any:
        """
        Send a completion request to Qwen engine with robust error/retry limits.
        """
        model = model_name or self.default_model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Initiating completion with {model} (temp={temperature}, stream={stream})")

        for attempt in range(1, self.max_retries + 1):
            try:
                if dashscope is None:
                    # Mock response for local development
                    logger.debug("dashscope SDK not installed. Returning mocked completion.")
                    return "Mocked response from Qwen-Max: AST analysis complete. Vulnerability resolved."

                response = dashscope.Generation.call(
                    model=model,
                    messages=messages,
                    result_format='message',
                    temperature=temperature,
                    stream=stream
                )
                
                # Check for standard DashScope status codes
                if response.status_code == 200:
                    return response.output.choices[0].message.content
                else:
                    raise RuntimeError(f"Dashscope API Error [{response.code}]: {response.message}")

            except Exception as e:
                logger.warning(f"Qwen Gateway attempt {attempt}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries:
                    raise e
                time.sleep(self.retry_backoff * attempt)

    def generate_stream(self, 
                        system_prompt: str, 
                        user_prompt: str, 
                        model_name: Optional[str] = None) -> Generator[str, None, None]:
        """
        Generate streaming responses from Qwen models.
        """
        model = model_name or self.default_model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if dashscope is None:
            yield "Mock stream chunk: resolving CWE..."
            return

        try:
            responses = dashscope.Generation.call(
                model=model,
                messages=messages,
                result_format='message',
                stream=True
            )
            for response in responses:
                if response.status_code == 200:
                    yield response.output.choices[0].message.content
                else:
                    raise RuntimeError(f"Streaming Error: {response.message}")
        except Exception as e:
            logger.error(f"Streaming failed: {str(e)}")
            raise e
