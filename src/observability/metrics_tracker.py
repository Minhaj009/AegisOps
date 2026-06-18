# -*- coding: utf-8 -*-
"""
AegisOps Metrics & Cost Tracker
===============================
Tracks execution metrics including token counts, Model Studio 
latencies, and estimated infrastructure/inference cost.
"""

import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger("AegisOps.MetricsTracker")

# Cost reference table (USD per 1M tokens) - based on typical model configurations
TOKEN_PRICING = {
    "qwen-max": {"input": 20.0, "output": 20.0},      # $20 per million
    "qwen-plus": {"input": 4.0, "output": 12.0},       # $4/input, $12/output per million
    "qwen-turbo": {"input": 1.0, "output": 3.0}        # $1/input, $3/output per million
}

class MetricsTracker:
    """Telemetry collector for token counts, call latencies, and estimated cost."""

    def __init__(self):
        self.call_records: List[Dict[str, Any]] = []

    def record_call(self, model: str, input_tokens: int, output_tokens: int, latency: float):
        """Record details of a single LLM api invocation."""
        pricing = TOKEN_PRICING.get(model.lower(), {"input": 0.0, "output": 0.0})
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000.0) * pricing["input"]
        output_cost = (output_tokens / 1_000_000.0) * pricing["output"]
        total_cost = input_cost + output_cost

        record = {
            "timestamp": time.time(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_seconds": latency,
            "estimated_cost_usd": total_cost
        }
        
        self.call_records.append(record)
        logger.info(f"Recorded LLM call: {model} | Latency: {latency:.2f}s | Cost: ${total_cost:.6f}")

    def get_summary(self) -> Dict[str, Any]:
        """Aggregate recorded metrics to compute overall totals."""
        total_calls = len(self.call_records)
        total_input_tokens = sum(r["input_tokens"] for r in self.call_records)
        total_output_tokens = sum(r["output_tokens"] for r in self.call_records)
        total_latency = sum(r["latency_seconds"] for r in self.call_records)
        total_cost = sum(r["estimated_cost_usd"] for r in self.call_records)
        
        avg_latency = total_latency / total_calls if total_calls > 0 else 0.0

        return {
            "total_calls": total_calls,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "average_latency_seconds": avg_latency,
            "total_estimated_cost_usd": total_cost
        }

if __name__ == "__main__":
    # Local runtime validation
    logging.basicConfig(level=logging.INFO)
    tracker = MetricsTracker()
    tracker.record_call("qwen-max", 1200, 450, 1.45)
    tracker.record_call("qwen-max", 3500, 1200, 3.12)
    
    summary = tracker.get_summary()
    print("\nMetrics summary:")
    print(f"Total Calls: {summary['total_calls']}")
    print(f"Total Input Tokens: {summary['total_input_tokens']}")
    print(f"Total Output Tokens: {summary['total_output_tokens']}")
    print(f"Average Latency: {summary['average_latency_seconds']:.2f}s")
    print(f"Total Estimated Cost: ${summary['total_estimated_cost_usd']:.6f}")
