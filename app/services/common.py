"""기능들이 같이 쓰는 도우미: 프롬프트 변수 만들기, 응답 메타 정보."""
from ..customize import Customize
from ..hcx import HCXResult

EMPTY = "(없음)"


def base_values(customize: Customize, relation: str | None = None, purpose: str | None = None) -> dict:
    """domain.yaml에서 관계·목적·격식 정보를 찾아 프롬프트 변수로 만듦."""
    domain = customize.domain()
    service = domain.get("service") or {}
    rel = customize.find("relations", relation)
    pur = customize.find("purposes", purpose)
    fml = customize.find("formality_levels", rel.get("formality"))
    return {
        "service_name": service.get("name", ""),
        "target": service.get("target", ""),
        "relation": rel.get("label") or EMPTY,
        "relation_note": rel.get("note") or EMPTY,
        "purpose": pur.get("label") or EMPTY,
        "formality": " - ".join(x for x in (fml.get("label"), fml.get("description")) if x) or EMPTY,
        "references": EMPTY,   # Step 6에서 채움
        "memory": EMPTY,       # Step 7에서 채움
    }


def setting(customize: Customize, key: str, default):
    return (customize.domain().get("settings") or {}).get(key, default)


def meta(*results: HCXResult) -> dict:
    """이번 요청에서 일어난 HCX 호출 요약 (프론트 토큰 표시용)."""
    calls = [{
        "model": r.model,
        "mock": r.mock,
        "cached": r.cached,
        "total_tokens": r.usage.get("totalTokens"),
        "latency_ms": r.latency_ms,
    } for r in results]
    return {"calls": calls, "total_tokens": sum(c["total_tokens"] or 0 for c in calls)}
