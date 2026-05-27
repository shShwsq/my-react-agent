from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ChatRequest, success
from app.services.text_service import TextService
from app.model_registry import get_default_url, build_request_url
from app.routers.models import get_config_api_key

router = APIRouter(prefix="/api/text", tags=["text"])

CHAT_KNOWN_FIELDS = {"messages", "model", "provider", "call_method", "category", "sub_category", "stream", "config_id", "base_url"}


@router.post("/completions")
async def text_completions(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    if request.config_id:
        try:
            config, api_key = get_config_api_key(request.config_id, current_user.id, db)
            request_url = get_default_url(config.provider, config.call_method, config.category, config.sub_category)
            if request.base_url:
                request_url = build_request_url(request.base_url, config.call_method)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        api_key = ""
        if request.base_url:
            request_url = build_request_url(request.base_url, request.call_method)
        else:
            request_url = get_default_url(request.provider, request.call_method, request.category, request.sub_category)
    
    request_data = request.model_dump()
    kwargs = {k: v for k, v in request_data.items() if k not in CHAT_KNOWN_FIELDS and v is not None}
    
    service = TextService()
    if request.stream:
        return StreamingResponse(
            service.stream_chat(
                request.messages,
                request.model,
                request.call_method,
                api_key,
                request_url,
                **kwargs,
            ),
            media_type="text/event-stream",
        )
    try:
        result = await service.chat(
            request.messages,
            request.model,
            request.call_method,
            api_key,
            request_url,
            **kwargs,
        )
        return success(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
