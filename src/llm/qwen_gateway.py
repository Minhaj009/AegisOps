# -*- coding: utf-8 -*-
"""
AegisOps Qwen LLM Gateway
=========================
API Grounding:
* Core Inference (Model Studio / Qwen Engine API): https://www.alibabacloud.com/help/en/model-studio/developer-reference/
* Qwen Cloud Base URL (Compatible Mode): https://dashscope-intl.aliyuncs.com/compatible-mode/v1
"""

import os
import logging
import asyncio
from http import HTTPStatus
from typing import Dict, Any, Generator, Optional, List
from dotenv import load_dotenv

# Try importing DashScope
try:
    import dashscope
except ImportError:
    dashscope = None

logger = logging.getLogger("AegisOps.QwenGateway")

class QwenGateway:
    """Core interface wrapper for Alibaba Cloud Model Studio (Qwen-Max/Qwen-Plus/Qwen-Flash)."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        # Load environment variables from .env
        load_dotenv()

        # Read DASHSCOPE_API_KEY. Throw an explicit, clear ValueError if missing.
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY is missing from the active environment. "
                "Ensure it is set in your environment variables or a local .env file."
            )

        # Apply to dashscope global config if available
        if dashscope:
            dashscope.api_key = self.api_key
            # The SDK calls base endpoint: https://dashscope-intl.aliyuncs.com/api/v1
            # Compatible with compatible-mode: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
            dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        # Default model settings
        self.default_model: str = "qwen-max"

    def generate_chat(self, 
                      system_prompt: str, 
                      user_prompt: str, 
                      model_name: Optional[str] = None, 
                      temperature: float = 0.2) -> str:
        """
        Send a completion request to the Qwen engine synchronously.
        """
        if not dashscope:
            raise RuntimeError(
                "DashScope SDK is not installed. Please run 'pip install -r requirements.txt'."
            )

        model = model_name or self.default_model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Initiating completion with {model} (temp={temperature})")

        try:
            response = dashscope.Generation.call(
                model=model,
                messages=messages,
                result_format='message',
                temperature=temperature,
                api_key=self.api_key
            )
            
            if response is None:
                raise RuntimeError("DashScope API call returned None response.")

            # Validate response status code using HTTPStatus enum
            if response.status_code == HTTPStatus.OK:
                try:
                    return response.output.choices[0].message.content
                except (AttributeError, IndexError) as e:
                    raise RuntimeError(f"Unexpected response structure: {str(e)}") from e
            else:
                raise RuntimeError(
                    f"DashScope API Error (Status: {response.status_code}, "
                    f"Code: {getattr(response, 'code', 'N/A')}): "
                    f"{getattr(response, 'message', 'No error details provided')}"
                )
        except Exception as e:
            logger.error(f"Sync generation call failed: {str(e)}")
            if not isinstance(e, RuntimeError):
                raise RuntimeError(f"DashScope invocation failed: {str(e)}") from e
            raise

    async def generate_remediation_async(self, 
                                         system_prompt: str, 
                                         user_prompt: str, 
                                         model_name: Optional[str] = None, 
                                         temperature: float = 0.2) -> str:
        """
        Send a completion request to the Qwen engine asynchronously using standard coroutines.
        """
        return await asyncio.to_thread(
            self.generate_chat,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=model_name,
            temperature=temperature
        )
