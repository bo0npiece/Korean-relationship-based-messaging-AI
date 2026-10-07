"""④ 리허설: AI가 상대 역할을 맡아 대화 연습 → 끝나면 피드백 리포트."""
from fastapi import HTTPException

from ..hcx import text_message
from .common import EMPTY, base_values, find_contact, meta, remember, setting


def _scenario(core, scenario_id: str) -> dict:
    for item in core.customize.domain().get("scenarios") or []:
        if item.get("id") == scenario_id:
            return item
    raise HTTPException(404, "domain.yaml에 없는 시나리오입니다.")


def _session(core, session_id: str) -> dict:
    session = core.rehearsals.get(session_id)
    if session is None:
        raise HTTPException(404, "없는 리허설입니다.")
    return session


def _values(core, scenario: dict, contact: dict | None) -> dict:
    values = base_values(core.customize, scenario.get("relation"))
    values.update(
        scenario_title=scenario.get("title", ""),
        ai_role=scenario.get("ai_role") or values["relation"],
        situation=scenario.get("situation") or EMPTY,
        goal=scenario.get("goal") or EMPTY,
    )
    if contact:
        values["memory"] = core.memory.memory_text(contact, values["relation"])
    return values


def _public(scenario: dict) -> dict:
    return {k: scenario.get(k) for k in ("id", "title", "ai_role", "situation", "goal")}


async def start(core, scenario_id: str, contact_id: int | None = None) -> dict:
    scenario = _scenario(core, scenario_id)
    find_contact(core, contact_id)
    session_id = core.rehearsals.create(scenario_id, contact_id)
    if scenario.get("opening"):
        core.rehearsals.add_turn(session_id, "assistant", scenario["opening"])
    return {"session_id": session_id, "scenario": _public(scenario), "messages": core.rehearsals.turns(session_id)}


async def send(core, session_id: str, text: str) -> dict:
    session = _session(core, session_id)
    if session["status"] != "active":
        raise HTTPException(409, "이미 끝난 리허설입니다.")
    scenario = _scenario(core, session["scenario_id"])
    contact = find_contact(core, session["contact_id"])
    core.rehearsals.add_turn(session_id, "user", text)

    # 슬라이딩 윈도우: 최근 N개 메시지만 보내서 토큰 절약
    window = int(setting(core.customize, "rehearsal_window", 8))
    recent = core.rehearsals.turns(session_id)[-window:]
    system = core.customize.prompt("rehearsal_role", **_values(core, scenario, contact))
    messages = [text_message("system", system)] + [text_message(t["role"], t["content"]) for t in recent]
    result = await core.hcx.chat("rehearsal", messages, max_tokens=300, temperature=0.7, use_cache=False)

    reply = result.text.strip()
    core.rehearsals.add_turn(session_id, "assistant", reply)
    return {"reply": reply, "meta": meta(result)}


async def end(core, session_id: str) -> dict:
    session = _session(core, session_id)
    if session["status"] == "ended":
        return {"session_id": session_id, **session["report"]}  # 다시 눌러도 재호출 안 함
    turns = core.rehearsals.turns(session_id)
    if not any(t["role"] == "user" for t in turns):
        raise HTTPException(422, "대화를 한 번 이상 한 뒤 종료해 주세요.")

    scenario = _scenario(core, session["scenario_id"])
    contact = find_contact(core, session["contact_id"])
    values = _values(core, scenario, contact)
    speaker = {"user": "사용자", "assistant": values["ai_role"]}
    transcript = "\n".join(f"{speaker[t['role']]}: {t['content']}" for t in turns)

    # 전체 대화를 HCX-007 Structured Outputs로 평가
    system = core.customize.prompt("rehearsal_feedback", **values)
    result = await core.hcx.chat_json("rehearsal_feedback", system, transcript,
                                      core.customize.schema("rehearsal_feedback"))
    report = {"report": result.data, "transcript": turns, "meta": meta(result)}
    core.rehearsals.finish(session_id, report)
    remember(core, contact, "rehearsal", scenario.get("title", ""), result.data.get("summary", ""))
    return {"session_id": session_id, **report}


def get(core, session_id: str) -> dict:
    session = _session(core, session_id)
    return {**session, "messages": core.rehearsals.turns(session_id)}
