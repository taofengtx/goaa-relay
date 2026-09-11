# AIKA1-OLLAMA-WINDOWS-SETUP-20260510
## Ollama Installation on Windows (AiKa-1)

**Status:** Ollama not yet installed (download in progress or manual installation required)

---

## Option 1: Manual Download & Install (Recommended)

1. Visit: https://ollama.com/download
2. Click: Download for Windows
3. Save as: C:\tmp\OllamaSetup.exe
4. Double-click to install
5. Follow installer wizard (default location: C:\Users\[UserName]\AppData\Local\Programs\Ollama)

## Option 2: Windows Package Manager

```powershell
winget install Ollama.Ollama
```

## Option 3: Chocolatey

```powershell
choco install ollama
```

## Verify Installation

After installation, verify in PowerShell:

```powershell
ollama --version
```

Expected output: `ollama version 0.x.x`

## Pull Model

```powershell
ollama pull qwen2.5:7b
```

## Verify Model

```powershell
ollama list
```

## Test Router

```powershell
cd C:\Users\Administrator\Projects\goaa-ai-local
python3 services\model-router\router.py
```
