from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ASRRequest, TTSRequest, success
from app.services.voice_service import VoiceService
from app.model_registry import get_default_url, build_request_url
from app.routers.models import get_config_api_key

router = APIRouter(prefix="/api/voice", tags=["voice"])

ASR_KNOWN_FIELDS = {"audio_data", "model", "provider", "call_method", "config_id", "base_url", "audio_format", "stream"}
TTS_KNOWN_FIELDS = {"text", "model", "provider", "call_method", "config_id", "base_url", "voice", "audio_format", "sample_rate", "stream"}


@router.post("/asr")
async def speech_to_text(
    request: ASRRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    if request.config_id:
        try:
            config, api_key = get_config_api_key(request.config_id, current_user.id, db)
            request_url = get_default_url(config.provider, config.call_method, "voice", "asr")
            if request.base_url:
                request_url = build_request_url(request.base_url, config.call_method)
            model = config.model_name
            call_method = config.call_method
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        api_key = ""
        model = request.model
        call_method = request.call_method
        if request.base_url:
            request_url = build_request_url(request.base_url, request.call_method)
        else:
            request_url = get_default_url(request.provider, request.call_method, "voice", "asr")
    
    request_data = request.model_dump()
    kwargs = {k: v for k, v in request_data.items() if k not in ASR_KNOWN_FIELDS and v is not None}
    
    service = VoiceService()
    
    if request.stream:
        return StreamingResponse(
            service.stream_asr(
                audio_data=request.audio_data,
                model=model,
                call_method=call_method,
                api_key=api_key,
                url=request_url,
                **kwargs,
            ),
            media_type="text/event-stream",
        )
    
    try:
        result = await service.asr(
            audio_data=request.audio_data,
            model=model,
            call_method=call_method,
            api_key=api_key,
            url=request_url,
            **kwargs,
        )
        return success(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    if request.config_id:
        try:
            config, api_key = get_config_api_key(request.config_id, current_user.id, db)
            request_url = get_default_url(config.provider, config.call_method, "voice", "tts")
            if request.base_url:
                request_url = build_request_url(request.base_url, config.call_method)
            model = config.model_name
            call_method = config.call_method
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        api_key = ""
        model = request.model
        call_method = request.call_method
        if request.base_url:
            request_url = build_request_url(request.base_url, request.call_method)
        else:
            request_url = get_default_url(request.provider, request.call_method, "voice", "tts")
    
    request_data = request.model_dump()
    kwargs = {k: v for k, v in request_data.items() if k not in TTS_KNOWN_FIELDS and v is not None}
    
    service = VoiceService()
    
    if request.stream:
        media_type = f"audio/{request.audio_format}"
        return StreamingResponse(
            service.stream_tts(
                text=request.text,
                model=model,
                call_method=call_method,
                api_key=api_key,
                url=request_url,
                voice=request.voice,
                audio_format=request.audio_format,
                sample_rate=request.sample_rate,
                **kwargs,
            ),
            media_type=media_type,
        )
    
    try:
        result = await service.tts(
            text=request.text,
            model=model,
            call_method=call_method,
            api_key=api_key,
            url=request_url,
            voice=request.voice,
            audio_format=request.audio_format,
            sample_rate=request.sample_rate,
            **kwargs,
        )
        return success(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
