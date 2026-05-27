from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional

from app.auth import get_current_user
from app.database import get_db
from app.models import User, ModelConfig
from app.schemas import ModelConfigCreate, success, fail, ErrorCode
from app.model_registry import PROVIDER_CALL_METHODS, PROVIDER_URLS, get_provider_call_methods, get_model_categories, get_model_names

router = APIRouter(prefix="/api/models", tags=["models"])


def get_config_api_key(config_id: int, user_id: int, db: Session) -> tuple[ModelConfig, str]:
    config = db.query(ModelConfig).filter(
        ModelConfig.id == config_id,
        or_(
            ModelConfig.user_id == user_id,
            ModelConfig.is_public == True,
        )
    ).first()
    
    if not config:
        raise ValueError("模型配置不存在或无权访问")
    
    if not config.api_key:
        raise ValueError("该模型配置未设置 API Key")
    
    return config, config.api_key


@router.get("/categories")
def get_categories():
    return success(get_model_categories())


@router.get("/providers")
def get_providers(category: str, sub_category: Optional[str] = None):
    if sub_category:
        key = f"{category}_{sub_category}"
    else:
        key = category
    
    category_config = PROVIDER_URLS.get(key, {})
    providers = []
    for provider in category_config.keys():
        providers.append({
            "value": provider,
            "label": provider,
        })
    return success(providers)


@router.get("/call-methods")
def get_call_methods(category: str, sub_category: Optional[str] = None, provider: str = "aliyun"):
    return success(get_provider_call_methods(category, sub_category, provider))


@router.get("/model-names")
def get_model_names_list(category: str, sub_category: Optional[str] = None, provider: str = "aliyun", call_method: str = "chat"):
    return success(get_model_names(provider, call_method, category, sub_category))


@router.get("/configs")
def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    configs = db.query(ModelConfig).filter(
        or_(
            ModelConfig.user_id == current_user.id,
            ModelConfig.is_public == True,
        )
    ).all()
    return success([{
        "id": c.id,
        "category": c.category,
        "sub_category": c.sub_category,
        "model_name": c.model_name,
        "provider": c.provider,
        "call_method": c.call_method,
        "has_api_key": bool(c.api_key),
        "base_url": c.base_url,
        "is_default": c.is_default,
        "is_public": c.is_public,
    } for c in configs])


@router.post("/configs")
def create_config(
    data: ModelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.is_default:
        query = db.query(ModelConfig).filter(
            ModelConfig.user_id == current_user.id,
            ModelConfig.category == data.category,
            ModelConfig.is_default == True,
        )
        if data.sub_category:
            query = query.filter(ModelConfig.sub_category == data.sub_category)
        query.update({"is_default": False})
    is_public = data.is_public if current_user.is_super else False
    config = ModelConfig(
        user_id=current_user.id,
        category=data.category,
        sub_category=data.sub_category,
        model_name=data.model_name,
        provider=data.provider,
        call_method=data.call_method,
        api_key=data.api_key,
        base_url=data.base_url,
        is_default=data.is_default,
        is_public=is_public,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return success({
        "id": config.id,
        "category": config.category,
        "sub_category": config.sub_category,
        "model_name": config.model_name,
        "provider": config.provider,
        "call_method": config.call_method,
        "has_api_key": bool(config.api_key),
        "base_url": config.base_url,
        "is_default": config.is_default,
        "is_public": config.is_public,
    }, "配置创建成功")


@router.put("/configs/{config_id}")
def update_config(
    config_id: int,
    data: ModelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id, ModelConfig.user_id == current_user.id).first()
    if not config:
        raise fail(ErrorCode.NOT_FOUND, "配置不存在")
    if data.is_default:
        query = db.query(ModelConfig).filter(
            ModelConfig.user_id == current_user.id,
            ModelConfig.category == data.category,
            ModelConfig.is_default == True,
        )
        if data.sub_category:
            query = query.filter(ModelConfig.sub_category == data.sub_category)
        query.update({"is_default": False})
    config.category = data.category
    config.sub_category = data.sub_category
    config.model_name = data.model_name
    config.provider = data.provider
    config.call_method = data.call_method
    if data.api_key:
        config.api_key = data.api_key
    config.base_url = data.base_url
    config.is_default = data.is_default
    if current_user.is_super:
        config.is_public = data.is_public
    db.commit()
    db.refresh(config)
    return success({
        "id": config.id,
        "category": config.category,
        "sub_category": config.sub_category,
        "model_name": config.model_name,
        "provider": config.provider,
        "call_method": config.call_method,
        "has_api_key": bool(config.api_key),
        "base_url": config.base_url,
        "is_default": config.is_default,
        "is_public": config.is_public,
    }, "配置更新成功")


@router.delete("/configs/{config_id}")
def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id, ModelConfig.user_id == current_user.id).first()
    if not config:
        raise fail(ErrorCode.NOT_FOUND, "配置不存在")
    db.delete(config)
    db.commit()
    return success(message="配置删除成功")
