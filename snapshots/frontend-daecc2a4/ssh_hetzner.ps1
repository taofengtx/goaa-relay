#!/usr/bin/env pwsh

# Hetzner 凭证
$sshHost = "5.78.76.21"
$sshUser = "root"
$sshPass = "tPAhqWCnTviW"

# 诊断命令
$diagCmd = @"
ls -lh /opt/goaa/downloads/
echo '---'
systemctl status openclaw --no-pager | grep Active
echo '---'
curl -s http://localhost:18789/health
"@

Write-Host "尝试连接 $sshHost..."

# 使用 ssh 命令直接执行
$result = & ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "${sshUser}@${sshHost}" $diagCmd 2>&1

Write-Host "=== SSH 诊断输出 ==="
Write-Host $result
