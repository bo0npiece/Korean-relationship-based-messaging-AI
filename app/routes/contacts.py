"""⑤ /api/contacts — 상대 프로필 CRUD + 지난 기록(interactions). 다른 기능에 contact_id로 연결."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core import Core
from ..deps import get_core, require_team_key

router = APIRouter(prefix="/api/contacts", tags=["contacts"], dependencies=[Depends(require_team_key)])


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="예: 김민수 교수님")
    relation: str | None = Field(default=None, max_length=50, description="domain.yaml relations의 id")
    profile: str | None = Field(default=None, max_length=1000, description="성격, 선호, 주의할 점 등 메모")


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    relation: str | None = Field(default=None, max_length=50)
    profile: str | None = Field(default=None, max_length=1000)


def _found(contact):
    if contact is None:
        raise HTTPException(404, "없는 상대입니다.")
    return contact


@router.get("")
async def list_contacts(core: Core = Depends(get_core)):
    return core.contacts.list_contacts()


@router.post("")
async def create_contact(body: ContactCreate, core: Core = Depends(get_core)):
    return core.contacts.create_contact(body.name, body.relation, body.profile)


@router.get("/{contact_id}")
async def get_contact(contact_id: int, core: Core = Depends(get_core)):
    return _found(core.contacts.get_contact(contact_id))


@router.put("/{contact_id}")
async def update_contact(contact_id: int, body: ContactUpdate, core: Core = Depends(get_core)):
    return _found(core.contacts.update_contact(contact_id, **body.model_dump()))


@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, core: Core = Depends(get_core)):
    if not core.contacts.delete_contact(contact_id):
        raise HTTPException(404, "없는 상대입니다.")
    return {"deleted": True}


@router.get("/{contact_id}/interactions")
async def list_interactions(contact_id: int, limit: int = 20, core: Core = Depends(get_core)):
    _found(core.contacts.get_contact(contact_id))
    return core.contacts.list_interactions(contact_id, min(max(limit, 1), 100))
