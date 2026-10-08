"""③ POST /api/interpret — 받은 메시지(텍스트/캡처) → 의도·감정·답장 초안."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..core import Core
from ..deps import get_core, require_team_key
from ..hcx.image import MAX_BYTES, prepare_image
from ..services.interpret import interpret

router = APIRouter(prefix="/api", tags=["interpret"], dependencies=[Depends(require_team_key)])


@router.post("/interpret")
async def post_interpret(
    text: str = Form(default="", max_length=3000, description="받은 메시지 (캡처만 올리면 비워도 됨)"),
    image: UploadFile | None = File(default=None, description="받은 메시지 캡처 (선택)"),
    relation: str | None = Form(default=None),
    contact_id: int | None = Form(default=None),
    core: Core = Depends(get_core),
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
    return await interpret(core, text.strip() or None, image_b64, relation or None, contact_id)
