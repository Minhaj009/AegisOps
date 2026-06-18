# -*- coding: utf-8 -*-
"""
AegisOps Structured Logging Utility
===================================
Formats logging records into standard JSON objects to capture 
agent reasoning steps, messages, and framework latency metrics.
"""

import sys
import json
import logging
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Formats log messages as single-line JSON items."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }

        # Embed extra attributes if explicitly supplied to logger.info(..., extra={...})
        if hasattr(record, "agent_name"):
            log_payload["agent_name"] = getattr(record, "agent_name")
        if hasattr(record, "task_id"):
            log_payload["task_id"] = getattr(record, "task_id")
        if hasattr(record, "reasoning_step"):
            log_payload["reasoning_step"] = getattr(record, "reasoning_step")
            
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)

def setup_logger(name: str = "AegisOps", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns the structured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Avoid duplicate handlers if setup is run multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger

if __name__ == "__main__":
    # Local runtime validation
    log = setup_logger("AegisOps.TestLogger")
    log.info("Initialized structured observability logging system.")
    log.info("Lead Auditor Agent identified CWE-79", extra={
        "agent_name": "LeadAuditorAgent",
        "task_id": "task_482937",
        "reasoning_step": "Codebase ingestion parse complete. Initiating regex scanning rules."
    })
