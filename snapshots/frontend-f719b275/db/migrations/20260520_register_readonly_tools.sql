-- ════════════════════════════════════════════════════════════════════════
-- P1.2.2 — Register 6 Read-Only Worker Tools
-- ════════════════════════════════════════════════════════════════════════
--
-- 簽發: 2026-05-20 PT Claude
-- 進度表: docs/development/GOAA_DEV_ROADMAP__v1_1__f7fc4d8e.md → P1.2.2
-- 規範遵守: #11 only-add (ON CONFLICT DO NOTHING) / #14 v2 git-then-DO /
--           #24 接口契約 / #25 跨層型別 / #36 v2 真實 agent.py exec_* 對齊
--
-- 部署: docker exec goaa-postgres psql -U goaa -d goaa -f <this_file>
-- 驗證: SELECT COUNT(*) FROM tools;  → 應該從 2 變 8
-- 回滾: DELETE FROM tools WHERE id IN ('health_check', 'ollama_status',
--       'docker_status', 'system_status', 'ping_test', 'log_summary');
--
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ──────────────────────────────────────────────────────────
-- Tool 1: health_check
-- 對應 agent.py exec_health_check
-- ──────────────────────────────────────────────────────────
INSERT INTO tools (id, name, description, parameters, handler_module, category, requires_node_id, is_active)
VALUES (
    'health_check',
    'Worker Health Check',
    'Returns worker agent uptime, version, and basic liveness signal. Read-only, no side effects.',
    '{
        "type": "object",
        "properties": {},
        "required": []
    }'::jsonb,
    'services.worker-agent.agent.exec_health_check',
    'query',
    true,
    true
)
ON CONFLICT (id) DO NOTHING;

-- ──────────────────────────────────────────────────────────
-- Tool 2: ollama_status
-- 對應 agent.py exec_ollama_status
-- ──────────────────────────────────────────────────────────
INSERT INTO tools (id, name, description, parameters, handler_module, category, requires_node_id, is_active)
VALUES (
    'ollama_status',
    'Ollama Service Status',
    'Returns Ollama daemon status, loaded models, and memory usage on the target worker. Read-only.',
    '{
        "type": "object",
        "properties": {},
        "required": []
    }'::jsonb,
    'services.worker-agent.agent.exec_ollama_status',
    'query',
    true,
    true
)
ON CONFLICT (id) DO NOTHING;

-- ──────────────────────────────────────────────────────────
-- Tool 3: docker_status
-- 對應 agent.py exec_docker_status
-- 規範 #18: agent.py 已用 shutil.which 預檢, 避免 Windows FileNotFoundError
-- ──────────────────────────────────────────────────────────
INSERT INTO tools (id, name, description, parameters, handler_module, category, requires_node_id, is_active)
VALUES (
    'docker_status',
    'Docker Containers Status',
    'Returns running Docker containers and their status. Read-only. Gracefully handles missing docker binary.',
    '{
        "type": "object",
        "properties": {},
        "required": []
    }'::jsonb,
    'services.worker-agent.agent.exec_docker_status',
    'query',
    true,
    true
)
ON CONFLICT (id) DO NOTHING;

-- ──────────────────────────────────────────────────────────
-- Tool 4: system_status
-- 對應 agent.py exec_system_status
-- ──────────────────────────────────────────────────────────
INSERT INTO tools (id, name, description, parameters, handler_module, category, requires_node_id, is_active)
VALUES (
    'system_status',
    'System Resource Status',
    'Returns OS, CPU usage, memory, disk usage, load average, and uptime. Read-only.',
    '{
        "type": "object",
        "properties": {},
        "required": []
    }'::jsonb,
    'services.worker-agent.agent.exec_system_status',
    'query',
    true,
    true
)
ON CONFLICT (id) DO NOTHING;

-- ──────────────────────────────────────────────────────────
-- Tool 5: ping_test
-- 對應 agent.py exec_ping_test
-- ──────────────────────────────────────────────────────────
INSERT INTO tools (id, name, description, parameters, handler_module, category, requires_node_id, is_active)
VALUES (
    'ping_test',
    'Network Ping Test',
    'Pings a target host and returns latency and packet loss. Read-only network probe.',
    '{
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "Target hostname or IP to ping (default: 8.8.8.8)"
            },
            "count": {
                "type": "integer",
                "description": "Number of ping packets (default: 4, max: 10)",
                "default": 4,
                "minimum": 1,
                "maximum": 10
            }
        },
        "required": []
    }'::jsonb,
    'services.worker-agent.agent.exec_ping_test',
    'query',
    true,
    true
)
ON CONFLICT (id) DO NOTHING;

-- ──────────────────────────────────────────────────────────
-- Tool 6: log_summary
-- 對應 agent.py exec_log_summary
-- 規範 #22: path allowlist (worker 端強制), 不接受任意路徑
-- ──────────────────────────────────────────────────────────
INSERT INTO tools (id, name, description, parameters, handler_module, category, requires_node_id, is_active)
VALUES (
    'log_summary',
    'Log Summary',
    'Returns tail of specified log file with optional grep filter. Worker enforces path allowlist for security. Read-only.',
    '{
        "type": "object",
        "properties": {
            "log_name": {
                "type": "string",
                "description": "Log identifier from worker allowlist (e.g. model-router, qwenpaw)"
            },
            "tail_lines": {
                "type": "integer",
                "description": "Number of trailing lines (default: 50, max: 500)",
                "default": 50,
                "minimum": 1,
                "maximum": 500
            },
            "grep_pattern": {
                "type": "string",
                "description": "Optional regex to filter matching lines"
            }
        },
        "required": ["log_name"]
    }'::jsonb,
    'services.worker-agent.agent.exec_log_summary',
    'query',
    true,
    true
)
ON CONFLICT (id) DO NOTHING;

-- ──────────────────────────────────────────────────────────
-- 驗證: 看新註冊的 6 個 + 原有 2 個
-- ──────────────────────────────────────────────────────────
SELECT id, name, category, requires_node_id, is_active
FROM tools
WHERE id IN ('health_check', 'ollama_status', 'docker_status',
             'system_status', 'ping_test', 'log_summary',
             'task_status', 'tasks_by_type')
ORDER BY id;

-- 總數應該是 8
SELECT COUNT(*) AS total_tools FROM tools;

COMMIT;
