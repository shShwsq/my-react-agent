from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional, Callable

from app.auth import get_current_user
from app.models import User
from app.schemas import success
from app.agents.task_agent import TaskAgent

router = APIRouter(prefix="/api/agents/task", tags=["task-agent"])

task_agent = TaskAgent()


class ExecuteTaskRequest(BaseModel):
    task_type: str
    input_data: Any
    context: Optional[dict] = None


class RegisterHandlerRequest(BaseModel):
    task_type: str
    handler_info: dict


@router.get("/status")
def get_task_status(
    current_user: User = Depends(get_current_user),
):
    return success(task_agent.get_status())


@router.post("/execute")
async def execute_task(
    request: ExecuteTaskRequest,
    current_user: User = Depends(get_current_user),
):
    result = await task_agent.execute_task(
        task_type=request.task_type,
        input_data=request.input_data,
        context=request.context
    )
    return success(result)


@router.get("/handlers")
def get_handlers(
    current_user: User = Depends(get_current_user),
):
    return success(list(task_agent.task_handlers.keys()))


@router.post("/handlers")
def register_handler(
    request: RegisterHandlerRequest,
    current_user: User = Depends(get_current_user),
):
    task_agent.register_handler(request.task_type, lambda x, c: request.handler_info)
    return success({"message": f"处理器已注册: {request.task_type}"})


@router.get("/capabilities")
def get_capabilities(
    current_user: User = Depends(get_current_user),
):
    return success(task_agent.get_capabilities())
