from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional

from app.auth import get_current_user
from app.models import User
from app.schemas import success, fail, ErrorCode
from app.agents.agent_manager import AgentManager

router = APIRouter(prefix="/api/agents", tags=["agents"])

agent_manager = AgentManager()


class PipelineRequest(BaseModel):
    user_input: str
    context: Optional[dict] = None


class AgentTaskRequest(BaseModel):
    task_type: str
    input_data: Any
    description: Optional[str] = None
    context: Optional[dict] = None


@router.get("/status")
def get_all_agents_status(
    current_user: User = Depends(get_current_user),
):
    return success(agent_manager.get_all_agents_status())


@router.get("/status/{agent_type}")
def get_agent_status(
    agent_type: str,
    current_user: User = Depends(get_current_user),
):
    status = agent_manager.get_agent_status(agent_type)
    if not status:
        raise fail(ErrorCode.NOT_FOUND, f"智能体类型 {agent_type} 不存在")
    return success(status)


@router.post("/pipeline")
async def run_full_pipeline(
    request: PipelineRequest,
    current_user: User = Depends(get_current_user),
):
    result = await agent_manager.full_pipeline(
        user_input=request.user_input,
        context=request.context
    )
    return success(result)


@router.post("/process")
async def process_with_brain(
    request: PipelineRequest,
    current_user: User = Depends(get_current_user),
):
    result = await agent_manager.process_with_brain(
        user_input=request.user_input,
        context=request.context
    )
    return success(result)


@router.post("/task")
async def create_agent_task(
    request: AgentTaskRequest,
    current_user: User = Depends(get_current_user),
):
    result = await agent_manager.process_with_task_agent(
        task_type=request.task_type,
        input_data=request.input_data,
        context=request.context
    )
    return success(result)


@router.post("/check")
async def check_result(
    request: AgentTaskRequest,
    current_user: User = Depends(get_current_user),
):
    criteria = request.context.get("check_criteria") if request.context else None
    result = await agent_manager.check_result(
        result=request.input_data,
        criteria=criteria
    )
    return success(result)


@router.post("/reset")
def reset_agents(
    current_user: User = Depends(get_current_user),
):
    agent_manager.reset_all_agents()
    return success({"message": "所有智能体已重置"})
