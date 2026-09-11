#!/bin/bash
# AIKA1-ROUTER-TEST-20260510: Test ROUTER-20260510-001 on AiKa-1
# Execute on AiKa-1 after Ollama installation
# Verify routing logic with local fallback

set -e

echo "=== Testing ROUTER-20260510-001 on AiKa-1 ==="
echo ""
echo "Objective: Verify routing logic with local fallback"
echo "Environment: AiKa-1 (192.168.1.207)"
echo ""

cd ~/Projects/goaa-ai-local

echo "[TEST] Running router.py with test scenarios..."
python3 services/model-router/router.py

echo ""
echo "=== Router Test Complete ==="
echo ""
echo "Expected Results:"
echo "✅ DeepSeek (85%): Default execution"
echo "✅ Claude (5%): P0/P1 high-risk only"
echo "✅ Ollama (10%): Local fallback @ 192.168.1.207:11434"
