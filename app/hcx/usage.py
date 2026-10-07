"""호출 기록: data/usage_log.jsonl 에 한 줄씩 추가."""
import json
from datetime import datetime, timezone
from pathlib import Path


class UsageLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, *, feature: str, kind: str, model: str, mock: bool, cached: bool,
               status: str, usage: dict | None = None, latency_ms: int = 0, error: str | None = None):
        usage = usage if isinstance(usage, dict) else {}
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "feature": feature,          # 기능명 (coach, compose ...)
            "kind": kind,                # chat / json / image / embed
            "model": model,
            "mock": mock,
            "cached": cached,
            "status": status,            # ok / error
            "prompt_tokens": usage.get("promptTokens"),
            "completion_tokens": usage.get("completionTokens"),
            "total_tokens": usage.get("totalTokens"),
            "latency_ms": latency_ms,
            "error": error,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def live_totals(self) -> dict:
        """실제 API 호출 횟수(실패 포함)와 누적 토큰. 한도 검사용."""
        live = [r for r in self.records() if not r["mock"] and not r["cached"]]
        return {
            "live_calls": len(live),
            "total_tokens": sum(r["total_tokens"] or 0 for r in live),
        }
