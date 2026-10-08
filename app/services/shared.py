"""여러 기능이 같이 쓰는 도우미: 프롬프트 변수 만들기, 상대 찾기·기록 저장, 응답 meta."""
from fastapi import HTTPException

from ..customize import Customize
from ..hcx import HCXResult
from .knowledge import format_references

EMPTY = "(없음)"


def domain_values(customize: Customize, relation: str | None = None, purpose: str | None = None) -> dict:
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


def domain_setting(customize: Customize, key: str, default):
    return (customize.domain().get("settings") or {}).get(key, default)


def call_meta(*results: HCXResult) -> dict:
    """이번 요청에서 일어난 HCX 호출 요약 (프론트 토큰 표시용)."""
    calls = [{
        "model": r.model,
        "mock": r.mock,
        "cached": r.cached,
        "total_tokens": r.usage.get("totalTokens"),
        "latency_ms": r.latency_ms,
    } for r in results]
    return {"calls": calls, "total_tokens": sum(c["total_tokens"] or 0 for c in calls)}


def find_contact(core, contact_id: int | None) -> dict | None:
    if contact_id is None:
        return None
    contact = core.contacts.get_contact(contact_id)
    if contact is None:
        raise HTTPException(404, "없는 상대입니다.")
    return contact


async def build_prompt_values(core, query: str, relation: str | None = None, purpose: str | None = None,
                  contact: dict | None = None):
    """프롬프트 변수 + 참고 자료({references}) + 관계 메모리({memory}). (values, references 목록) 반환."""
    if contact and not relation:
        relation = contact.get("relation")  # 관계를 안 고르면 상대 프로필의 관계 사용
    values = domain_values(core.customize, relation, purpose)
    if contact:
        values["memory"] = core.contacts.memory_text(contact, values["relation"],
                                                   domain_setting(core.customize, "memory_recent", 3))
    hits = await core.knowledge.search(query, domain_setting(core.customize, "knowledge_top_k", 3))
    if hits:
        values["references"] = format_references(hits)
    refs = [{"title": h["title"], "source": h["source"], "score": h["score"]} for h in hits]
    return values, refs


def save_interaction(core, contact: dict | None, feature: str, input_text: str, output_text: str):
    """상대를 지정했으면 이번 대화를 기록 (다음 요청의 {memory}에 반영)."""
    if contact:
        core.contacts.add_interaction(contact["id"], feature, input_text, output_text)
