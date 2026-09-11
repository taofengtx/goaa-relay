#!/bin/bash
# AIKA1-OLLAMA-SETUP-20260510: Install Ollama as local fallback for Model Router
# Execute on AiKa-1 (192.168.1.207) - QwenPaw Scheduler & Router Hub
# Target: Establish local fallback & cost governance baseline

set -e

echo "=== AiKa-1 Ollama Setup (ROUTER-20260510-001) ==="
echo ""
echo "Target: Establish local fallback for model router"
echo "Router Location: AiKa-1 (192.168.1.207)"
echo "QwenPaw Coordinator: AiKa-1"
echo ""

# Step 1: Install Ollama
echo "[STEP 1] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh
echo "✅ Ollama installed"
echo ""

# Step 2: Start Ollama service
echo "[STEP 2] Starting Ollama service..."
sudo systemctl start ollama
sleep 3
sudo systemctl status ollama --no-pager
echo "✅ Ollama service running"
echo ""

# Step 3: Pull Qwen2.5 7B model
echo "[STEP 3] Pulling Qwen2.5:7B model (this may take 5-10 minutes)..."
ollama pull qwen2.5:7b
echo "✅ Qwen2.5:7B model ready"
echo ""

# Step 4: Verify installation
echo "[STEP 4] Verifying Ollama installation..."
echo ""
echo "Available models:"
curl -s http://localhost:11434/api/tags | python3 -m json.tool
echo ""
echo "=== AiKa-1 Ollama Setup Complete ==="
echo ""
echo "Status: ✅ Ready for ROUTER-20260510-001"
echo "Local Fallback: Qwen2.5:7B on 192.168.1.207:11434"
echo "Router Integration: services/model-router/router.py"
