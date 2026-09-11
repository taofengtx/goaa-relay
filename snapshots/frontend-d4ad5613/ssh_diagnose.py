#!/usr/bin/env python3
import subprocess
import sys

host = "5.78.76.21"
user = "root"
password = "knbsMfVtACjg"

commands = [
    "ls -lh /opt/goaa/downloads/",
    "echo '---'",
    "systemctl status openclaw --no-pager | grep Active",
    "echo '---'",
    "curl -s http://localhost:18789/health"
]

# Join all commands with &&
cmd_str = " && ".join(commands)

# Use sshpass if available, otherwise use paramiko
try:
    import paramiko
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=30)
    
    stdin, stdout, stderr = client.exec_command(cmd_str)
    output = stdout.read().decode() + stderr.read().decode()
    
    print(output)
    client.close()
except ImportError:
    # Fallback: try sshpass
    try:
        result = subprocess.run(
            f'sshpass -p "{password}" ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 {user}@{host} "{cmd_str}"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
