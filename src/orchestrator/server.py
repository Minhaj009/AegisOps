# -*- coding: utf-8 -*-
"""
AegisOps Web Dashboard Server
=============================
A dependency-free HTTP server that serves the dashboard UI and streams
state-machine transitions via Server-Sent Events (SSE).
"""

import os
import sys
import json
import queue
import logging
import urllib.parse
import threading
import asyncio
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import subprocess
import time
from typing import Dict, Any, Optional

# Add workspace path to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.orchestrator.router import AegisOpsRouter

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AegisOps.Server")

DASHBOARD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard"))

approval_event = threading.Event()
approval_decision = None

def request_approval_callback() -> str:
    global approval_decision
    approval_event.clear()
    approval_decision = None
    logger.info("[APPROVAL GATE] Pausing pipeline and waiting for developer input (Approve/Reject)...")
    approval_event.wait()
    logger.info(f"[APPROVAL GATE] Pipeline unblocked. User decision: {approval_decision}")
    return approval_decision

class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """Handles static file routing and SSE progress streams."""


    def _serve_static(self, filepath: str, content_type: str) -> None:
        """Helper to serve static files from dashboard directory."""
        if not os.path.exists(filepath):
            self.send_error(404, f"File not found: {os.path.basename(filepath)}")
            return
            
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logger.error(f"Error serving {filepath}: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")

    def do_GET(self) -> None:
        """GET router endpoint."""
        global approval_decision
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # 1. API: Trigger pipeline with SSE stream
        if path == "/api/run":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            target_path = query_params.get("target", [""])[0]
            mode = query_params.get("mode", ["autopilot"])[0]
            
            if not target_path:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing 'target' parameter."}).encode("utf-8"))
                return
                
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            logger.info(f"Triggering remediation pipeline via SSE for: {target_path} (mode={mode})")
            
            # Queue to stream events from the pipeline thread to the handler thread
            event_queue = queue.Queue()
            
            # Status callback to put events into the queue
            def status_callback(state: str, message: str, data: Dict[str, Any]) -> None:
                event_queue.put({
                    "state": state,
                    "message": message,
                    "data": data
                })
                
            # Target running function in separate thread
            def pipeline_thread_worker():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                router = AegisOpsRouter()
                try:
                    loop.run_until_complete(router.run_pipeline(
                        target_path=target_path,
                        status_callback=status_callback,
                        mode=mode,
                        approval_callback=request_approval_callback
                    ))
                except Exception as ex:
                    logger.error(f"Pipeline crashed: {str(ex)}")
                    status_callback("ERROR", f"Orchestrator Exception: {str(ex)}", {})
                finally:
                    event_queue.put(None)  # Sentinel to close stream
                    loop.close()
                    
            t = threading.Thread(target=pipeline_thread_worker)
            t.daemon = True
            t.start()
            
            # Read queue and stream to client
            while True:
                item = event_queue.get()
                if item is None:
                    break
                try:
                    self.wfile.write(f"data: {json.dumps(item)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except (ConnectionResetError, ConnectionAbortedError) as ce:
                    logger.warning(f"Client disconnected: {str(ce)}")
                    break
                except Exception as e:
                    logger.error(f"Error streaming event: {str(e)}")
                    break
            return
            
        # 1.5 API: Interactive Co-Pilot Gates
        elif path == "/api/approve":
            approval_decision = "APPROVE"
            approval_event.set()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "approved"}).encode("utf-8"))
            return
            
        elif path == "/api/reject":
            approval_decision = "REJECT"
            approval_event.set()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "rejected"}).encode("utf-8"))
            return
            
        # 2. Static Content Routing
        if path == "/":
            self._serve_static(os.path.join(DASHBOARD_DIR, "index.html"), "text/html")
        elif path == "/style.css":
            self._serve_static(os.path.join(DASHBOARD_DIR, "style.css"), "text/css")
        elif path == "/app.js":
            self._serve_static(os.path.join(DASHBOARD_DIR, "app.js"), "application/javascript")
        elif path == "/logo.png":
            self._serve_static(os.path.join(DASHBOARD_DIR, "logo.png"), "image/png")
        else:
            self.send_error(404, "Page not found")

def clear_port(port: int) -> None:
    """Finds and kills any processes listening on the specified port (cross-platform)."""
    import platform
    try:
        my_pid = str(os.getpid())
        if platform.system() == "Windows":
            output = subprocess.check_output("netstat -ano", shell=True).decode("utf-8")
            pids = set()
            for line in output.strip().split("\n"):
                if "LISTENING" in line and f":{port}" in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pids.add(parts[-1])
            for pid in pids:
                if pid != my_pid and pid != "0":
                    logger.info(f"Port {port} is occupied by process {pid}. Terminating it...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux/macOS: use fuser to find and kill
            result = subprocess.run(f"fuser {port}/tcp", shell=True, capture_output=True, text=True)
            pids = result.stdout.strip().split()
            for pid in pids:
                pid = pid.strip()
                if pid and pid != my_pid:
                    logger.info(f"Port {port} is occupied by process {pid}. Terminating it...")
                    subprocess.run(f"kill -9 {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    except Exception as e:
        logger.debug(f"Error checking/clearing port {port}: {str(e)}")

def start_server(port: int = 8000) -> None:
    """Starts the multi-threaded HTTP server with port auto-clearing."""
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    clear_port(port)
    server_address = ("", port)
    try:
        httpd = ThreadingHTTPServer(server_address, DashboardHTTPHandler)
    except OSError as e:
        logger.warning(f"Failed to bind to port {port} ({str(e)}). Retrying port clear...")
        clear_port(port)
        httpd = ThreadingHTTPServer(server_address, DashboardHTTPHandler)
        
    logger.info(f"==================================================")
    logger.info(f" AegisOps Real-Time Dashboard Running on Port {port}")
    logger.info(f" Access URL: http://localhost:{port}")
    logger.info(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down server gracefully...")
        httpd.server_close()

if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_server(port_arg)
