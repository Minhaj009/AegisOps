# -*- coding: utf-8 -*-
"""
AegisOps LLM Gateway Smoke Test
===============================
Verifies both synchronous and asynchronous pipelines of the QwenGateway wrapper.
"""

import sys
import asyncio
from src.llm.qwen_gateway import QwenGateway

def run_sync_test(gateway: QwenGateway, system_prompt: str, user_prompt: str, model: str) -> None:
    print("[SYNC] Initiating synchronous smoke test...")
    try:
        response = gateway.generate_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=model
        )
        print(f"[SYNC] Received response: '{response}'")
        if response.strip() == "READY":
            print("[SYNC] SUCCESS: Gateway returned 'READY' successfully!")
        else:
            print(f"[SYNC] WARNING: Gateway response did not match 'READY'. Got: '{response}'")
    except Exception as e:
        print(f"[SYNC] ERROR: Synchronous gateway call failed: {str(e)}")
        raise

async def run_async_test(gateway: QwenGateway, system_prompt: str, user_prompt: str, model: str) -> None:
    print("[ASYNC] Initiating asynchronous smoke test...")
    try:
        response = await gateway.generate_remediation_async(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=model
        )
        print(f"[ASYNC] Received response: '{response}'")
        if response.strip() == "READY":
            print("[ASYNC] SUCCESS: Gateway returned 'READY' successfully!")
        else:
            print(f"[ASYNC] WARNING: Gateway response did not match 'READY'. Got: '{response}'")
    except Exception as e:
        print(f"[ASYNC] ERROR: Asynchronous gateway call failed: {str(e)}")
        raise

def main() -> None:
    print("=== AegisOps LLM Gateway Integration Smoke Test ===")
    
    # Check if API key is in environment or .env file before running
    # The QwenGateway initializer will raise ValueError if it's missing.
    try:
        gateway = QwenGateway()
    except ValueError as ve:
        print(f"\n[CONFIGURATION ERROR] {str(ve)}")
        print("Please supply your DASHSCOPE_API_KEY in a .env file or your environment variables.")
        sys.exit(1)
        
    model = "qwen-turbo"
    system_prompt = "You are the AegisOps kernel validation sub-routine. Respond with 'READY'."
    user_prompt = "Verify connection status."
    
    # 1. Run Synchronous Call
    run_sync_test(gateway, system_prompt, user_prompt, model)
    
    # 2. Run Asynchronous Call
    asyncio.run(run_async_test(gateway, system_prompt, user_prompt, model))
    
    print("=== Smoke Test Finished ===")

if __name__ == "__main__":
    main()
