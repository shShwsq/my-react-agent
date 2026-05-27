from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional

from app.auth import get_current_user
from app.models import User
from app.schemas import success
from app.agents.check_agent import CheckAgent

router = APIRouter(prefix="/api/agents/check", tags=["check-agent"])

check_agent = CheckAgent()


class ValidateRequest(BaseModel):
    result: Any
    criteria: Optional[dict] = None


class QualityCheckRequest(BaseModel):
    content: str


class SuggestRequest(BaseModel):
    result: Any
    issues: list[str]


@router.get("/status")
def get_check_status(
    current_user: User = Depends(get_current_user),
):
    return success(check_agent.get_status())


@router.post("/validate")
async def validate_result(
    request: ValidateRequest,
    current_user: User = Depends(get_current_user),
):
    result = await check_agent.validate_result(request.result, request.criteria or {})
    return success(result)


@router.post("/quality")
async def quality_check(
    request: QualityCheckRequest,
    current_user: User = Depends(get_current_user),
):
    result = await check_agent.quality_check(request.content)
    return success(result)


@router.post("/suggest")
async def suggest_improvements(
    request: SuggestRequest,
    current_user: User = Depends(get_current_user),
):
    result = await check_agent.suggest_improvements(request.result, request.issues)
    return success(result)


@router.post("/add-rule")
def add_check_rule(
    rule_type: str,
    rule: dict,
    current_user: User = Depends(get_current_user),
):
    check_agent.add_check_rule(rule_type, rule)
    return success({"message": f"检查规则已添加: {rule_type}"})


@router.get("/capabilities")
def get_capabilities(
    current_user: User = Depends(get_current_user),
):
    return success(check_agent.get_capabilities())
