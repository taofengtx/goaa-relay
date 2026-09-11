"""
GOAA.AI Model Router v1.0
Task: ROUTER-20260510-001
"""

from datetime import datetime, timedelta
import json, os

# ── 模型定價（2026-05 實際報價）──────────────────
MODEL_PRICING = {
    "claude-sonnet-4-6": {
        "input_per_1k":  0.003,
        "output_per_1k": 0.015,
        "role": "architecture_pm",
        "max_priority": 1,   # 只處理 P0/P1
    },
    "deepseek-v4-flash": {
        "input_per_1k":  0.00014,
        "output_per_1k": 0.00028,
        "role": "daily_worker",
        "max_priority": 4,
    },
    "ollama-qwen-32b": {
        "input_per_1k":  0.0,
        "output_per_1k": 0.0,
        "role": "fallback",
        "max_priority": 4,
    },
}

# ── 熔斷閾值 ──────────────────────────────────────
CIRCUIT_BREAKER = {
    "hourly_cost_limit": 2.0,      # 每小時超過 $2 → 禁用高成本模型
    "single_call_review": 0.05,    # 單次超過 $0.05 → 需要審批
    "daily_cost_limit": 10.0,      # 每日超過 $10 → 告警
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {})
    input_cost  = (input_tokens  / 1000) * pricing.get("input_per_1k", 0)
    output_cost = (output_tokens / 1000) * pricing.get("output_per_1k", 0)
    return round(input_cost + output_cost, 6)

def get_optimal_model(task_priority: int, risk_level: int,
                      estimated_tokens: int = 1000) -> dict:
    """
    路由邏輯：
    P0/P1 + 高風險 → Claude（架構決策、安全問題）
    P2-P4           → DeepSeek（日常任務）
    熔斷觸發        → Ollama（本地備援）
    """
    print(f"[Router] Running... priority={task_priority}, risk={risk_level}")
    hourly_cost = get_hourly_cost()
    print(f"[Router] Hourly cost: ${hourly_cost:.2f}")

    # 熔斷：每小時成本超標
    if hourly_cost > CIRCUIT_BREAKER["hourly_cost_limit"]:
        return {
            "model": "ollama-qwen-32b",
            "reason": f"circuit_breaker: hourly_cost ${hourly_cost:.2f} exceeded",
            "review_required": False,
        }

    # P0/P1 高風險任務 → Claude
    if task_priority <= 1 and risk_level >= 3:
        model = "claude-sonnet-4-6"
    # P0/P1 低風險 → DeepSeek
    elif task_priority <= 1:
        model = "deepseek-v4-flash"
    # P2-P4 → DeepSeek
    else:
        model = "deepseek-v4-flash"

    estimated_cost = estimate_cost(model, estimated_tokens, estimated_tokens // 2)
    review_required = estimated_cost > CIRCUIT_BREAKER["single_call_review"]

    return {
        "model": model,
        "estimated_cost_usd": estimated_cost,
        "review_required": review_required,
        "reason": f"priority={task_priority} risk={risk_level}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

def get_hourly_cost(log_file: str = None) -> float:
    """讀取過去1小時的 API 消耗"""
    if log_file is None:
        # Auto-detect platform
        import platform
        if platform.system() == "Windows":
            log_file = r"C:\tmp\goaa_api_usage.log"
        else:
            log_file = "/opt/goaa/logs/api_usage.log"
    
    try:
        if not os.path.exists(log_file):
            return 0.0
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        total = 0.0
        with open(log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry["timestamp"].replace("Z", ""))
                    if ts > one_hour_ago:
                        total += entry.get("cost_usd", 0)
                except:
                    pass
        return total
    except Exception as e:
        print(f"[Warning] Failed to read cost log: {e}")
        return 0.0

def log_usage(model: str, input_tokens: int, output_tokens: int,
              task_id: str = "", log_file: str = None):
    """記錄每次 API 調用"""
    if log_file is None:
        # Auto-detect platform
        import platform
        if platform.system() == "Windows":
            log_file = r"C:\tmp\goaa_api_usage.log"
        else:
            log_file = "/opt/goaa/logs/api_usage.log"
    
    try:
        cost = estimate_cost(model, input_tokens, output_tokens)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "task_id": task_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
        }
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return cost
    except Exception as e:
        print(f"[Warning] Failed to log usage: {e}")
        return estimate_cost(model, input_tokens, output_tokens)

# ── 測試 ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("GOAA Model Router - ROUTER-20260510-001")
    print("=" * 60)
    print()
    
    tests = [
        {"priority": 0, "risk": 4, "desc": "P0 高風險安全問題"},
        {"priority": 0, "risk": 2, "desc": "P0 低風險功能請求"},
        {"priority": 2, "risk": 1, "desc": "P2 日常任務"},
        {"priority": 3, "risk": 1, "desc": "P3 日誌分析"},
    ]
    
    for i, t in enumerate(tests, 1):
        print(f"[Test {i}] {t['desc']}")
        print(f"         Priority={t['priority']}, Risk={t['risk']}")
        
        result = get_optimal_model(t["priority"], t["risk"])
        
        print(f"         → Model: {result['model']}")
        print(f"         → Est. Cost: ${result['estimated_cost_usd']:.6f}")
        print(f"         → Review Required: {result['review_required']}")
        print(f"         → Reason: {result.get('reason', 'N/A')}")
        print()
    
    print("=" * 60)
    print("✅ Router Test Complete")
    print("=" * 60)
