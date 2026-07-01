#!/bin/bash
# =============================================================================
# AegisOps - Alibaba Cloud ECS Deployment Script
# =============================================================================
# This script deploys the AegisOps dashboard and orchestration engine
# on an Alibaba Cloud ECS instance (Ubuntu/Debian).
#
# Usage:
#   1. SSH into your Alibaba Cloud ECS instance
#   2. Clone the repo: git clone https://github.com/Minhaj009/AegisOps.git
#   3. cd AegisOps
#   4. Copy your .env file: cp .env.example .env && nano .env  (fill in your keys)
#   5. Run: chmod +x deploy/deploy_ecs.sh && ./deploy/deploy_ecs.sh
# =============================================================================

set -e

echo "=============================================="
echo "  AegisOps - Alibaba Cloud ECS Deployment"
echo "=============================================="

# ── 1. System Dependencies ──────────────────────────────────────────────────
echo "[1/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv git docker.io psmisc > /dev/null 2>&1

# Enable Docker for sandbox containers
sudo systemctl start docker 2>/dev/null || true
sudo systemctl enable docker 2>/dev/null || true

# ── 2. Python Virtual Environment ───────────────────────────────────────────
echo "[2/6] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# ── 3. Install Python Dependencies ──────────────────────────────────────────
echo "[3/6] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ── 4. Validate Environment Configuration ───────────────────────────────────
echo "[4/6] Validating environment configuration..."
if [ ! -f ".env" ]; then
    echo ""
    echo "  ⚠️  ERROR: .env file not found!"
    echo "  Run: cp .env.example .env && nano .env"
    echo "  Then fill in your DASHSCOPE_API_KEY and ALIBABA_WORKSPACE_ID."
    echo ""
    exit 1
fi

# Quick check for placeholder values
if grep -q "your_alibaba_cloud_api_key_here" .env 2>/dev/null; then
    echo ""
    echo "  ⚠️  WARNING: DASHSCOPE_API_KEY still contains the placeholder value."
    echo "  Edit .env and replace it with your actual API key from:"
    echo "  https://dashscope.console.aliyun.com/apiKey"
    echo ""
    exit 1
fi

echo "  ✓ Environment configuration validated."

# ── 5. Open Firewall Port ───────────────────────────────────────────────────
echo "[5/6] Configuring firewall for port 8000..."
# Try ufw first, then iptables as fallback
if command -v ufw &> /dev/null; then
    sudo ufw allow 8000/tcp > /dev/null 2>&1 || true
else
    sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT 2>/dev/null || true
fi
echo "  ✓ Port 8000 opened."

# ── 6. Launch AegisOps Dashboard Server ─────────────────────────────────────
echo "[6/6] Starting AegisOps Dashboard Server..."
echo ""

# Kill any existing AegisOps process
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# Get the server's public IP for the access URL
PUBLIC_IP=$(curl -s --connect-timeout 3 http://100.100.100.200/latest/meta-data/eip 2>/dev/null || \
            curl -s --connect-timeout 3 http://100.100.100.200/latest/meta-data/public-ipv4 2>/dev/null || \
            curl -s --connect-timeout 3 https://ifconfig.me 2>/dev/null || \
            echo "YOUR_SERVER_IP")

# Start server in background with nohup
nohup python3 src/orchestrator/server.py 8000 > aegisops_server.log 2>&1 &
SERVER_PID=$!

sleep 2

# Verify server started
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "=============================================="
    echo "  ✅ AegisOps Successfully Deployed!"
    echo "=============================================="
    echo ""
    echo "  Dashboard URL:  http://${PUBLIC_IP}:8000"
    echo "  Server PID:     ${SERVER_PID}"
    echo "  Server Log:     ./aegisops_server.log"
    echo ""
    echo "  To view logs:   tail -f aegisops_server.log"
    echo "  To stop:        kill ${SERVER_PID}"
    echo ""
    echo "  ⚡ Take a screenshot of this terminal AND"
    echo "     the dashboard in your browser for Devpost!"
    echo "=============================================="
else
    echo "  ❌ Server failed to start. Check logs:"
    echo "     cat aegisops_server.log"
    exit 1
fi
