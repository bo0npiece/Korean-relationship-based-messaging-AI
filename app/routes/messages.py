"""POST /api/compose, POST /api/interpret"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..customize import Customize
from ..deps import get_customize, get_hcx, require_team_key
from ..hcx import HCXClient
from ..hcx.image import MAX_BYTES, prepare_image
from ..services.compose import compose
from ..services.interpret import interpret

router = APIRouter(prefix="/api", tags=["messages"], dependencies=[Depends(require_team_key)])


class ComposeRequest(BaseModel):
    key_points: str = Field(min_length=1, max_length=2000, description="전하고 싶은 핵심 내용")
    relation: str | None = None
    purpose: str | None = None


@router.post("/compose")
async def post_compose(body: ComposeRequest, hcx: HCXClient = Depends(get_hcx),
                       customize: Customize = Depends(get_customize)):
    return await compose(hcx, customize, body.key_points, body.relation, body.purpose)


@router.post("/interpret")
async def post_interpret(
    text: str = Form(default="", max_length=3000, description="받은 메시지 (캡처만 올리면 비워도 됨)"),
    image: UploadFile | None = File(default=None, description="받은 메시지 캡처 (선택)"),
    relation: str | None = Form(default=None),
    hcx: HCXClient = Depends(get_hcx),
    customize: Customize = Depends(get_customize),
):
    image_b64 = None
    if image is not None and image.filename:
        raw = await image.read(MAX_BYTES + 1)
        try:
            image_b64 = prepare_image(raw)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
    if not text.strip() and not image_b64:
        raise HTTPException(422, "받은 메시지 텍스트나 캡처 이미지 중 하나는 필요합니다.")
    return await interpret(hcx, customize, text.strip() or None, image_b64, relation or None)
