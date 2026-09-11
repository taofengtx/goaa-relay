"""
db.py — PostgreSQL 連線層 (GOAA Phase 4)
設計: 不檢查 pg_ready(), 直接 try/except 操作
"""
import logging, os
from contextlib import contextmanager

logger = logging.getLogger("goaa.db")

try:
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool
    from psycopg2.extras import Json, RealDictCursor
    PG_AVAILABLE = True
except ImportError:
    logger.warning("psycopg2 not installed")
    PG_AVAILABLE = False

PG_CONFIG = {
    "host": os.getenv("PG_HOST", "127.0.0.1"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "database": os.getenv("PG_DB", "goaa"),
    "user": os.getenv("PG_USER", "goaa"),
    "password": os.environ["PG_PASSWORD"],
}

_pool = None

def init_pool(minconn=1, maxconn=5):
    global _pool
    if not PG_AVAILABLE:
        return False
    try:
        _pool = SimpleConnectionPool(minconn, maxconn, **PG_CONFIG)
        with _pool.getconn() as conn:
            conn.cursor().execute("SELECT 1")
            conn.commit()
        _pool.putconn(conn)
        logger.info("PG pool OK (%s/%s)", PG_CONFIG["host"], PG_CONFIG["database"])
        return True
    except Exception as e:
        logger.error("PG init failed: %s", e)
        _pool = None
        return False

@contextmanager
def get_conn():
    if _pool is None:
        raise RuntimeError("PG pool not init")
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)

def _exec(sql, params=None, fetch=True):
    """Execute SQL, return rows or True/False"""
    if _pool is None:
        return False
    try:
        with _pool.getconn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                if fetch:
                    rows = [dict(r) for r in cur.fetchall()]
                else:
                    rows = True
                conn.commit()
            _pool.putconn(conn)
        return rows
    except Exception as e:
        logger.error("DB error: %s", e)
        if _pool:
            try:
                _pool.putconn(conn)
            except:
                pass
        return False

def task_upsert(task_id, task_data):
    return _exec("""
        INSERT INTO tasks
            (id, task_type, worker_id, model_used, priority, status,
             payload, result, revenue_usd, cost_usd, duration_ms,
             error_msg, created_at, started_at, completed_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s)
        ON CONFLICT (id) DO UPDATE SET
            worker_id=EXCLUDED.worker_id, status=EXCLUDED.status,
            result=EXCLUDED.result, revenue_usd=EXCLUDED.revenue_usd,
            cost_usd=EXCLUDED.cost_usd, duration_ms=EXCLUDED.duration_ms,
            error_msg=EXCLUDED.error_msg,
            completed_at=EXCLUDED.completed_at
    """, (
        task_id,
        task_data.get("task_type","ops"),
        task_data.get("worker_id") or task_data.get("assigned_worker"),
        task_data.get("model_used") or task_data.get("model_required"),
        task_data.get("priority",5),
        task_data.get("status","pending"),
        Json(task_data.get("payload",{})),
        Json(task_data.get("result",{})),
        task_data.get("revenue_usd",0) or task_data.get("actual_revenue_usd",0),
        task_data.get("cost_usd",0) or task_data.get("actual_cost_usd",0),
        task_data.get("duration_ms",0),
        task_data.get("error_msg",""),
        task_data.get("started_at"),
        task_data.get("completed_at"),
    ), fetch=False)

def task_stats():
    r = _exec("""
        SELECT
            COUNT(*) FILTER (WHERE status='pending') AS pending,
            COUNT(*) FILTER (WHERE status='running') AS running,
            COUNT(*) FILTER (WHERE status IN ('success','completed','done')) AS done,
            COUNT(*) FILTER (WHERE status='failed') AS failed,
            COALESCE(SUM(revenue_usd) FILTER (WHERE created_at::date=CURRENT_DATE),0) AS rev,
            COALESCE(SUM(cost_usd) FILTER (WHERE created_at::date=CURRENT_DATE),0) AS cost
        FROM tasks
    """)
    if not r:
        return {"pending":0,"running":0,"done":0,"failed":0,"revenue_today":0,"cost_today":0,"profit_today":0}
    return {"pending":int(r[0]["pending"]),"running":int(r[0]["running"]),
            "done":int(r[0]["done"]),"failed":int(r[0]["failed"]),
            "revenue_today":float(r[0]["rev"]),"cost_today":float(r[0]["cost"]),
            "profit_today":float(r[0]["rev"])-float(r[0]["cost"])}

def task_worker_stats():
    r = _exec("""
        SELECT worker_id, COUNT(*) AS cnt,
               COALESCE(SUM(revenue_usd),0) AS rev,
               COALESCE(SUM(cost_usd),0) AS cost
        FROM tasks WHERE created_at::date=CURRENT_DATE AND worker_id IS NOT NULL
        GROUP BY worker_id
    """)
    if not r:
        return {}
    return {row["worker_id"]: {"tasks_today":row["cnt"],"revenue_today":float(row["rev"]),"cost_today":float(row["cost"])}
            for row in r}

def task_rebuild_pool():
    r = _exec("""
        SELECT id AS task_id, task_type, worker_id, status,
               payload::text, priority, created_at
        FROM tasks WHERE status IN ('pending','running','awaiting_approval')
        ORDER BY priority DESC, created_at ASC
    """)
    if not r:
        return []
    logger.info("Rebuilt %d tasks from PG", len(r))
    return r


# ============= Phase 4 sessions/messages 持久化 =============

def session_ensure(session_id, project_id=None, title=None):
    """確保 session 存在 (新或更新 last_message_at). 失敗返 False"""
    try:
        return _exec("""
            INSERT INTO sessions (id, project_id, title, started_at, last_message_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET last_message_at = NOW()
        """, (session_id, project_id, title or "Untitled"), fetch=False)
    except Exception as e:
        logger.error("session_ensure(%%s) failed: %%s", session_id, e)
        return False
def message_insert(session_id, role, content, model=None, tokens_in=0, tokens_out=0, cost_usd=0):
    """寫一條訊息到 messages 表. 失敗返 False"""
    if not session_id:
        return False
    try:
        # 確保 session 存在
        session_ensure(session_id)
        # 插入 message
        return _exec("""
            INSERT INTO messages (session_id, role, content, model_used,
                                 tokens_in, tokens_out, cost_usd, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (session_id, role, content, model, tokens_in, tokens_out, cost_usd), fetch=False)
    except Exception as e:
        logger.error("message_insert(%s, %s) failed: %s", session_id, role, e)
        return False

def messages_get(session_id, limit=50):
    """拉 session 的歷史訊息. 失敗返 []"""
    if not session_id:
        return []
    try:
        rows = _exec("""
            SELECT role, content, model_used, tokens_in, tokens_out,
                   cost_usd, created_at
            FROM messages
            WHERE session_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """, (session_id, limit))
        return rows if rows else []
    except Exception as e:
        logger.error("messages_get(%%s) failed: %%s", session_id, e)
        return []
def session_create(title=None, project_id=None):
    """創建新 session, 返回 session_id (UUID 字串). 失敗返 None"""
    import uuid as _uuid
    sid = str(_uuid.uuid4())
    if session_ensure(sid, project_id, title):
        return sid
    return None

def sessions_list(project_id=None, limit=50):
    """列 session (可篩 project_id). 失敗返 []"""
    if not pg_ready():
        return []
    try:
        with _exec() as cur:
            if project_id:
                cur.execute("""
                    SELECT id, project_id, title, started_at, last_message_at, archived
                    FROM sessions WHERE project_id = %s
                    ORDER BY last_message_at DESC LIMIT %s
                """, (project_id, limit))
            else:
                cur.execute("""
                    SELECT id, project_id, title, started_at, last_message_at, archived
                    FROM sessions
                    ORDER BY last_message_at DESC LIMIT %s
                """, (limit,))
            rows = cur.fetchall()
            return [
                {
                    "id": str(r[0]),
                    "project_id": str(r[1]) if r[1] else None,
                    "title": r[2],
                    "started_at": r[3].isoformat() if r[3] else None,
                    "last_message_at": r[4].isoformat() if r[4] else None,
                    "archived": r[5],
                }
                for r in rows
            ]
    except Exception as e:
        logger.error("sessions_list failed: %s", e)
        return []


# ───────────────────────────────────────────────
# P1.2.0 — tasks 反查 helper (規範 #36 v2 Runtime Truth)
# 立規: 2026-05-19, P1.2.0 patch
# ───────────────────────────────────────────────

def task_get_session_message(task_id: str):
    """從 task_id 反查 message_id + session_id (P1.2.1 依賴)"""
    try:
        rows = _exec(
            """
            SELECT
                payload->>'message_id' AS message_id,
                payload->>'session_id' AS session_id
            FROM tasks
            WHERE id = %s
            LIMIT 1
            """,
            (task_id,),
            fetch=True,
        )
        if not rows:
            return None
        row = rows[0]
        session_id = row.get("session_id")
        if not session_id:
            return None
        return {
            "message_id": row.get("message_id"),
            "session_id": session_id,
        }
    except Exception as e:
        logger.exception(f"task_get_session_message failed: task={task_id} err={e}")
        return None


def tasks_recent(limit: int = 50, status: str = None):
    """最近任務列表 (audit + Phase 1 驗收用)"""
    try:
        if status:
            rows = _exec(
                """
                SELECT id, task_type, worker_id, status, created_at, completed_at
                FROM tasks
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (status, limit),
                fetch=True,
            )
        else:
            rows = _exec(
                """
                SELECT id, task_type, worker_id, status, created_at, completed_at
                FROM tasks
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
                fetch=True,
            )
        return rows or []
    except Exception as e:
        logger.exception(f"tasks_recent failed: {e}")
        return []



# ════════════════════════════════════════════════════════════════════════
# P1.2.1 hook: tool_invocation_insert
# ════════════════════════════════════════════════════════════════════════
# Purpose: 將每次 tool 呼叫的 audit 記錄寫入 tool_invocations 表
# 規範遵守:
#   #11 only-add  : 純新增 helper, 不動現有
#   #18           : 自帶 try/except, 失敗 raise 讓呼叫方決定
#   #24           : 直接呼叫 _exec(), 不用 context manager
#   #25 跨層型別  : 顯式轉 UUID/json/None
#   #28 不靜默    : 失敗 logger.exception
# 呼叫者: api.py task_complete endpoint (P1.2.1 hook)
# 寫入失敗: 不 raise (規範 #18, 主流程不阻塞)
# ════════════════════════════════════════════════════════════════════════
def tool_invocation_insert(
    session_id,
    tool_call_id: str,
    args: dict = None,
    tool_id: str = None,
    message_id=None,
    agent_id=None,
    result: dict = None,
    duration_ms: int = None,
    error: str = None,
):
    """
    寫入 tool_invocations 表 (P1.2.1 audit trail).

    必填:
        session_id    (str|UUID) - 從 task_get_session_message(task_id) 拿
        tool_call_id  (str)      - 通常用 task_id

    可選:
        args          (dict)     - tool 呼叫參數, 預設 {}
        tool_id       (str)      - tools.id (FK), 不在 8 個註冊 tool 內傳 None
        message_id    (str|UUID) - 關聯訊息 id
        agent_id      (str|UUID) - 關聯 agent id
        result        (dict)     - tool 執行結果
        duration_ms   (int)      - 執行時長 ms
        error         (str)      - 錯誤訊息

    Returns:
        str: 新建的 tool_invocation id (uuid str), 或 None (失敗)
    """
    import uuid
    import json
    import logging
    logger = logging.getLogger(__name__)

    try:
        inv_id = str(uuid.uuid4())

        # session_id 規範化 (規範 #25 確定性轉換)
        # 目標: tool_invocations.session_id 是 UUID type, 非 UUID 字串會 PG 報錯
        # 策略: 如果 session_id 是有效 UUID → 直接使用; 否則 uuid5 確定性轉換
        if not isinstance(session_id, str):
            session_id_raw = str(session_id)
        else:
            session_id_raw = session_id
        try:
            # 嘗試解析為 UUID
            uuid.UUID(session_id_raw)
            session_id_str = session_id_raw
        except (ValueError, AttributeError):
            # 非標準 UUID → uuid5 確定性轉換 (規範 #25 跨層型別)
            session_id_str = str(uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"tool-invocations-sid:{session_id_raw}",
            ))
            logger.info(
                f"P1.2.1 session_id uuid5-converted: "
                f"{session_id_raw[:20]}... → {session_id_str[:12]}..."
            )

        # args / result jsonb 序列化 (規範 #25 顯式 jsonb)
        args_json = json.dumps(args or {})
        result_json = json.dumps(result) if result is not None else None

        # tool_id 規範化 (8 個註冊 tool 之外傳 None, FK 允許 NULL)
        # 防呆: 截斷到 50 字元 (varchar 50 限制)
        if tool_id and len(tool_id) > 50:
            logger.warning(f"P1.2.1 tool_id 截斷 {len(tool_id)} → 50: {tool_id[:50]}")
            tool_id = tool_id[:50]

        # tool_call_id 防呆 (varchar 100)
        if len(tool_call_id) > 100:
            logger.warning(f"P1.2.1 tool_call_id 截斷 {len(tool_call_id)} → 100")
            tool_call_id = tool_call_id[:100]

        # UUID 驗證 helper (message_id / agent_id 共用)
        def _p121_is_uuid(s):
            try:
                uuid.UUID(s)
                return True
            except (ValueError, AttributeError):
                return False

        # 規範 #24: 直接呼叫 _exec, 不用 with (對齊 db.py 風格)
        # 規範 #28: fetch=False 因為無 RETURNING, 避免 fetch timing bug
        _exec(
            """
            INSERT INTO tool_invocations
                (id, session_id, tool_call_id, args, tool_id,
                 message_id, agent_id, result, duration_ms, error)
            VALUES
                (%s::uuid, %s::uuid, %s, %s::jsonb, %s,
                 %s, %s, %s::jsonb, %s, %s)
            """,
            (
                inv_id,
                session_id_str,
                tool_call_id,
                args_json,
                tool_id,
                # message_id 和 agent_id 也需 UUID 規範化 (tool_invocations 表 UUID type)
                str(message_id) if message_id and _p121_is_uuid(str(message_id)) else None,
                str(agent_id) if agent_id and _p121_is_uuid(str(agent_id)) else None,
                result_json,
                duration_ms,
                error,
            ),
            fetch=False,
        )
        logger.info(
            f"P1.2.1 tool_invocation inserted: id={inv_id[:8]}... "
            f"tool_id={tool_id} duration_ms={duration_ms} "
            f"err={'yes' if error else 'no'}"
        )
        return inv_id

    except Exception as e:
        # 規範 #28 不靜默: 完整 traceback
        logger.exception(f"P1.2.1 tool_invocation_insert FAILED: {e}")
        # 規範 #18 不阻塞: 不 raise, 讓主流程繼續
        return None
