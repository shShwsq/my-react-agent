from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional

from app.auth import get_current_user
from app.models import User
from app.schemas import success
from app.agents.brain_agent import BrainAgent

router = APIRouter(prefix="/api/agents/brain", tags=["brain-agent"])

brain_agent = BrainAgent()


class AnalyzeIntentRequest(BaseModel):
    user_input: str
    context: Optional[dict] = None


class DispatchTaskRequest(BaseModel):
    task_id: str
    target_agent: str
    task_type: str
    input_data: Any
    description: Optional[str] = None


@router.get("/status")
def get_brain_status(
    current_user: User = Depends(get_current_user),
):
    return success(brain_agent.get_status())


@router.post("/analyze-intent")
async def analyze_intent(
    request: AnalyzeIntentRequest,
    current_user: User = Depends(get_current_user),
):
    result = await brain_agent.analyze_intent(request.user_input)
    return success(result)


@router.post("/dispatch")
async def dispatch_task(
    request: DispatchTaskRequest,
    current_user: User = Depends(get_current_user),
):
    from app.agents.base import AgentTask
    task = AgentTask(
        task_id=request.task_id,
        task_type=request.task_type,
        description=request.description or "",
        input_data=request.input_data,
    )
    result = await brain_agent.dispatch_task(task, request.target_agent)
    return success({
        "task_id": result.task_id,
        "status": result.status,
        "dispatched_to": result.metadata.get("dispatched_to") if result.metadata else None,
    })


@router.get("/capabilities")
def get_capabilities(
    current_user: User = Depends(get_current_user),
):
    return success(brain_agent.get_capabilities())
