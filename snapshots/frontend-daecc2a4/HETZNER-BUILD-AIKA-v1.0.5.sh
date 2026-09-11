#!/bin/bash  
# Quick build AiKa-Node v1.0.5 on Hetzner  
cd /tmp  
wget -q https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/aika-node-build-v1.0.5.sh  
chmod +x aika-node-build-v1.0.5.sh  
bash aika-node-build-v1.0.5.sh  
echo "=== Build Result ==="  
ls -lh /opt/goaa/downloads/aika-node*.deb  
