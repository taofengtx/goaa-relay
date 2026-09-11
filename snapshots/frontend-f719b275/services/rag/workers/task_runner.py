#!/usr/bin/env python3
"""
GOAA Worker Runtime V5.2.C-1 — Local Task Runner
部署: /opt/goaa/workers/task_runner.py
角色: AiKa-Box Pro Alpha 本地任務執行入口(入地第一步)。

職責:
  1. 讀取 task JSON(/opt/goaa/tasks/<name>.json,不含 secret)
  2. 依 task name dispatch 到 handler
  3. 呼叫 embed_worker.exec_embed_corpus
  4. 生成 task_result JSON(/opt/goaa/task_results/)
  5. 寫 runtime log(/opt/goaa/logs/)
  6. 輸出標準 JSON
  7. 不輸出正文(text_redacted)
  8. 不輸出 secret

安全:
  - secret 一律由 Tao 親手經 /etc/goaa/worker_secrets.env 注入進程環境。
  - task_runner 不讀 secrets.env 內容,不 printenv,不 cat corpus。
  - 執行: set -a; . /etc/goaa/worker_secrets.env; set +a; <venv>/python task_runner.py ...

第一版邊界(禁止):不接 DO Router、不 polling、不碰 dashboard、不做真 credits 結算。
"""

import os
import sys
import json
import time
import socket
import logging
import argparse
import datetime

# embed_worker 與本檔同目錄(/opt/goaa/workers/)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("task_runner")

TASKS_DIR = "/opt/goaa/tasks"
RESULTS_DIR = "/opt/goaa/task_results"
LOGS_DIR = "/opt/goaa/logs"
WORKER_ID = socket.gethostname()   # aika-core-01


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ── handler:exec_embed_corpus_full ──
def _handle_exec_embed_corpus_full(params: dict) -> dict:
    """
    包裝已驗證的 embed_worker.exec_embed_corpus 為正式本地任務。
    params(來自 task JSON,不含 secret):
      corpus_path, target_table, dry_run, limit, batch_size, model
    """
    from embed_worker import exec_embed_corpus
    inner = exec_embed_corpus({
        "corpus_path": params["corpus_path"],
        "target_table": params.get("target_table", "qwenpaw_memory_chunks"),
        "dry_run": params.get("dry_run", False),
        "limit": params.get("limit"),
        "batch_size": params.get("batch_size", 50),
        "model": params.get("model"),
    })
    # 只取統計,不取任何正文
    return inner.get("stats", {})


# ── handler:exec_topk_query_verify ──
def _handle_exec_topk_query_verify(params: dict) -> dict:
    """
    top-k 檢索驗證(不返正文)。params: query_text, top_k, target_table, model
    """
    from topk_query import exec_topk_query_verify
    inner = exec_topk_query_verify({
        "query_text": params["query_text"],
        "top_k": params.get("top_k", 5),
        "target_table": params.get("target_table", "qwenpaw_memory_chunks"),
        "model": params.get("model"),
    })
    return inner.get("stats", {})


# task name -> handler
TASK_HANDLERS = {
    "exec_embed_corpus_full": _handle_exec_embed_corpus_full,
    "exec_topk_query_verify": _handle_exec_topk_query_verify,
}


def run_task(task_name: str, task_id: str, params: dict) -> dict:
    started = _utc_now()
    t0 = time.time()

    handler = TASK_HANDLERS.get(task_name)
    if handler is None:
        raise ValueError(f"unknown task: {task_name} (known: {list(TASK_HANDLERS)})")

    status = "success"
    stats = {}
    err = None
    try:
        stats = handler(params)
    except Exception as e:
        status = "failed"
        err = f"{type(e).__name__}: {str(e)[:200]}"   # 截斷,避免任何意外洩漏
        log.error("task %s failed: %s", task_name, err)

    finished = _utc_now()
    duration = round(time.time() - t0, 2)

    # 標準 task_result(只含統計與中繼資料,無正文無 secret)
    result = {
        "task_id": task_id,
        "task": task_name,
        "worker_id": WORKER_ID,
        "status": status,
        "duration_s": stats.get("duration_s", duration),
        "credits_placeholder": None,   # 第一版不做真實 credits 結算
        "started_at": started,
        "finished_at": finished,
        "result_path": None,           # 下面填
        "log_path": None,              # 下面填
    }
    # 依 task 類型補欄位(無正文無 secret)
    if task_name == "exec_embed_corpus_full":
        result.update({
            "processed": stats.get("processed", 0),
            "inserted": stats.get("inserted", 0),
            "skipped_secret": stats.get("skipped_secret", 0),
            "skipped_empty": stats.get("skipped_empty", 0),
            "failed": stats.get("failed", 0),
            "dry_run": stats.get("dry_run", params.get("dry_run", False)),
            "corpus_path": params.get("corpus_path"),
            "target_table": params.get("target_table", "qwenpaw_memory_chunks"),
        })
    elif task_name == "exec_topk_query_verify":
        result.update({
            "query_text_hash": stats.get("query_text_hash"),
            "query_embedding_dim": stats.get("query_embedding_dim"),
            "top_k": stats.get("top_k"),
            "rows_returned": stats.get("rows_returned", 0),
            "matches": stats.get("matches", []),   # 只含 id/role/text_len/dim/distance,無正文
        })
    if err:
        result["error"] = err
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--params", required=True, help="task JSON 路徑(不含 secret)")
    args = ap.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOGS_DIR, f"{args.task}_{args.task_id}_{ts}.log")
    result_path = os.path.join(RESULTS_DIR, f"{args.task_id}.json")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(fh)

    log.info("=== task_runner start: task=%s task_id=%s worker=%s ===",
             args.task, args.task_id, WORKER_ID)

    # 讀 task JSON(不含 secret)
    try:
        with open(args.params, encoding="utf-8") as f:
            params = json.load(f)
    except Exception as e:
        log.error("讀取 task JSON 失敗: %s", type(e).__name__)
        print(json.dumps({"status": "failed",
                          "error": f"cannot read params: {type(e).__name__}"},
                         ensure_ascii=False))
        sys.exit(2)

    result = run_task(args.task, args.task_id, params)
    result["result_path"] = result_path
    result["log_path"] = log_path

    # 寫 task_result JSON
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    log.info("=== task_runner done: status=%s task=%s ===",
             result.get("status"), result.get("task"))

    # 標準 JSON 輸出(無正文、無 secret)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
