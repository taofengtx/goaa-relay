cd ~
echo "=== Installing Ollama on AiKa-2 ==="
curl -fsSL https://ollama.com/install.sh | sh
echo "✅ Ollama installed"
sudo systemctl start ollama
echo "✅ Ollama service started"
sleep 5
sudo systemctl status ollama
echo ""
echo "[STEP 2] Pulling Qwen:7b model..."
ollama pull qwen:7b
echo "✅ Qwen:7b pulled"
echo ""
echo "[STEP 3] Checking available models..."
curl http://localhost:11434/api/tags
echo ""
echo "=== Ollama Setup Complete ==="
