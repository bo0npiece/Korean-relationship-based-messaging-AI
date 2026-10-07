"""리허설: /api/rehearsal/start, /{id}/message, /{id}/end"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..core import Core
from ..deps import get_core, require_team_key
from ..services import rehearsal

router = APIRouter(prefix="/api/rehearsal", tags=["rehearsal"], dependencies=[Depends(require_team_key)])


class StartRequest(BaseModel):
    scenario_id: str = Field(description="domain.yaml scenarios의 id")
    contact_id: int | None = None


class MessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


@router.post("/start")
async def start(body: StartRequest, core: Core = Depends(get_core)):
    return await rehearsal.start(core, body.scenario_id, body.contact_id)


@router.post("/{session_id}/message")
async def message(session_id: str, body: MessageRequest, core: Core = Depends(get_core)):
    return await rehearsal.send(core, session_id, body.text)


@router.post("/{session_id}/end")
async def end(session_id: str, core: Core = Depends(get_core)):
    return await rehearsal.end(core, session_id)


@router.get("/{session_id}")
async def get(session_id: str, core: Core = Depends(get_core)):
    return rehearsal.get(core, session_id)
