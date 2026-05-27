from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ImageGenerationRequest, ImageUnderstandingRequest, success
from app.services.vision_service import VisionService
from app.model_registry import get_default_url, build_request_url
from app.routers.models import get_config_api_key

router = APIRouter(prefix="/api/vision", tags=["vision"])

IMAGE_GEN_KNOWN_FIELDS = {"prompt", "model", "provider", "call_method", "config_id", "base_url", "size", "n"}
IMAGE_UNDERSTANDING_KNOWN_FIELDS = {"messages", "model", "provider", "call_method", "config_id", "base_url", "stream", "image_url"}


@router.post("/generation")
async def image_generation(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    if request.config_id:
        try:
            config, api_key = get_config_api_key(request.config_id, current_user.id, db)
            request_url = get_default_url(config.provider, config.call_method, "vision", "image_generation")
            if request.base_url:
                request_url = build_request_url(request.base_url, config.call_method)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        api_key = ""
        if request.base_url:
            request_url = build_request_url(request.base_url, request.call_method)
        else:
            request_url = get_default_url(request.provider, request.call_method, "vision", "image_generation")
    
    request_data = request.model_dump()
    kwargs = {k: v for k, v in request_data.items() if k not in IMAGE_GEN_KNOWN_FIELDS and v is not None}
    
    service = VisionService()
    try:
        result = await service.image_generation(
            prompt=request.prompt,
            model=request.model,
            call_method=request.call_method,
            api_key=api_key,
            url=request_url,
            size=request.size,
            n=request.n,
            **kwargs,
        )
        return success(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/understanding")
async def image_understanding(
    request: ImageUnderstandingRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    if request.config_id:
        try:
            config, api_key = get_config_api_key(request.config_id, current_user.id, db)
            request_url = get_default_url(config.provider, config.call_method, "vision", "image_understanding")
            if request.base_url:
                request_url = build_request_url(request.base_url, config.call_method)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        api_key = ""
        if request.base_url:
            request_url = build_request_url(request.base_url, request.call_method)
        else:
            request_url = get_default_url(request.provider, request.call_method, "vision", "image_understanding")
    
    request_data = request.model_dump()
    kwargs = {k: v for k, v in request_data.items() if k not in IMAGE_UNDERSTANDING_KNOWN_FIELDS and v is not None}
    
    service = VisionService()
    
    if request.stream:
        return StreamingResponse(
            service.stream_image_understanding(
                messages=request.messages,
                model=request.model,
                call_method=request.call_method,
                api_key=api_key,
                url=request_url,
                image_url=request.image_url,
                **kwargs,
            ),
            media_type="text/event-stream",
        )
    
    try:
        result = await service.image_understanding(
            messages=request.messages,
            model=request.model,
            call_method=request.call_method,
            api_key=api_key,
            url=request_url,
            image_url=request.image_url,
            **kwargs,
        )
        return success(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
