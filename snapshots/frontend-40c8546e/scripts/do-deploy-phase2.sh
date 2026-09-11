#!/bin/bash
# DO-DEPLOY-20260510-001 - Phase 2
# GitHub Sync on DigitalOcean
# Execute via: ssh root@134.199.227.108 "bash -s" < do-deploy-phase2.sh

set -e

echo "=== Phase 2: GitHub Sync ==="
echo ""

cd /opt/goaa

# Initialize git if needed
if [ ! -d .git ]; then
    echo "[1/4] Initializing Git repository..."
    git init
    git remote add origin https://github.com/taofengtx/goaa-ai-frontend.git
    echo "✅ Git initialized"
else
    echo "[1/4] Git repository already exists"
fi

# Fetch latest
echo "[2/4] Fetching from GitHub..."
git fetch origin main -q
echo "✅ Fetched"

# Create/checkout do-node branch
echo "[3/4] Setting up do-node branch..."
git checkout -b do-node origin/main 2>/dev/null || git checkout do-node
echo "✅ Branch ready"

# Copy registration to docs
echo "[4/4] Registering node..."
mkdir -p /opt/goaa/docs/node-registry 2>/dev/null || true
cp /opt/goaa/runtime/registration.json /opt/goaa/docs/node-registry/akc-do-001.json 2>/dev/null || echo "Docs directory not available"

# Try to commit
git add docs/ 2>/dev/null || true
git commit -m "node: AKC-DO-001 DigitalOcean cloud worker deployed" 2>/dev/null || echo "No changes to commit"

echo ""
echo "=== Phase 2 Complete ==="
echo ""
echo "Node registration file location: /opt/goaa/runtime/registration.json"
echo "GitHub branch: do-node"
echo ""
