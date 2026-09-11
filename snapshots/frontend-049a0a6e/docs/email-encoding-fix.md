# 邮件编码修复指南 (EMAIL-ENCODING-20260509-001)

## 问题描述

OpenClaw 发送的邮件中文显示为乱码。原因是 `main.py` 中的 `MIMEText` 没有指定 UTF-8 编码。

## 根本原因

```python
# ❌ 错误方式 - 导致中文乱码
from email.mime.text import MIMEText
body = MIMEText(content)  # 默认 ASCII 编码
msg['Subject'] = subject  # 没有指定编码
```

## 修复方案

### 1. 在 /opt/goaa/main.py 中找到 send_email 函数

```bash
grep -n "def send_email\|MIMEText" /opt/goaa/main.py
```

### 2. 修改 MIMEText 调用

**改前：**
```python
from email.mime.text import MIMEText

body = MIMEText(content)
msg['Subject'] = subject
```

**改后：**
```python
from email.mime.text import MIMEText
from email.header import Header

# UTF-8 编码内容
body = MIMEText(content, 'plain', 'utf-8')
# UTF-8 编码主题
msg['Subject'] = Header(subject, 'utf-8')
```

### 3. 完整的修复脚本

将以下内容保存为 `/tmp/fix_email_encoding.py`：

```python
#!/usr/bin/env python3
import re

with open('/opt/goaa/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 MIMEText 编码
content = re.sub(
    r"MIMEText\(([^,)]+)\)(?!\,)",
    r"MIMEText(\1, 'plain', 'utf-8')",
    content
)

# 修复邮件头编码
if 'from email.header import Header' not in content:
    content = re.sub(
        r'(from email\.mime\..*\n)',
        r'\1from email.header import Header\n',
        content
    )

with open('/opt/goaa/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK')
```

### 4. 执行修复

```bash
ssh root@5.78.76.21 "python3 /tmp/fix_email_encoding.py && systemctl restart openclaw"
```

### 5. 验证修复

发送测试邮件：

```python
#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

msg = MIMEMultipart('alternative')
msg['Subject'] = Header('GOAA.AI 測試郵件 2026-05-09', 'utf-8')
msg['From'] = 'aika@goaa.ai'
msg['To'] = 'taofengtx@gmail.com'

body = MIMEText('中文測試：Hetzner 安全加固完成，AiKa-3 預留節點已配置。', 'plain', 'utf-8')
msg.attach(body)

with smtplib.SMTP('smtp.zoho.com', 587) as s:
    s.starttls()
    s.login('aika@goaa.ai', 'Ft009119$')
    s.send_message(msg)
    print('✅ 测试邮件已发送')
```

## 检查列表

- [ ] 登录 Hetzner VPS: `ssh root@5.78.76.21`
- [ ] 备份原始文件: `cp /opt/goaa/main.py /opt/goaa/main.py.bak.20260509`
- [ ] 执行修复脚本: `python3 /tmp/fix_email_encoding.py`
- [ ] 验证修复: `grep -n "MIMEText.*utf-8\|Header.*utf-8" /opt/goaa/main.py`
- [ ] 重启服务: `systemctl restart openclaw`
- [ ] 发送测试邮件验证
- [ ] 检查 Tao 师兄的邮箱 - 中文应该正确显示

## 预期结果

修复后，所有发送的邮件中文字符将正确显示，不再出现乱码。

## 相关配置

| 项目 | 值 |
|------|-----|
| SMTP 服务器 | smtp.zoho.com |
| SMTP 端口 | 587 |
| 发件人 | aika@goaa.ai |
| 字符编码 | UTF-8 |
| TLS | 启用 |

---

**修复时间**: 2026-05-09 10:00 UTC  
**修复人**: AiKa  
**状态**: 等待应用 ⏳
