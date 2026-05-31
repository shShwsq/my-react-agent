import json
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Optional, AsyncGenerator

from app.auth import get_current_user
from app.database import get_db, SessionLocal
from app.models import User, AgentFile, Message, Room
from app.schemas import success
from app.agents.brain_agent import BrainAgent
from app.agents.check_agent import CheckAgent
from app.agents.task_agent import TaskAgent
from app.tasks.tools import tool_registry
from app.routers.models import get_config_api_key
from app.model_registry import get_default_url, build_request_url
from app.services.variable_service import VariableService
from app.services.context_service import ContextService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents/loop", tags=["agent-loop"])

brain_agent = BrainAgent()
check_agent = CheckAgent()
task_agent = TaskAgent()


class LoopRequest(BaseModel):
    user_input: str
    room_id: str
    context: Optional[dict] = None
    max_iterations: int = 10
    enabled_tools: Optional[list[str]] = None


class AgentLoopOrchestrator:
    def __init__(self):
        self.brain = brain_agent
        self.check = check_agent
        self.task = task_agent
        self._paused_rooms: dict[str, bool] = {}
        # 环境变量等待机制：room_id -> {"event": asyncio.Event, "values": dict}
        self._env_var_waiters: dict[str, dict] = {}
    
    def pause_room(self, room_id: str):
        self._paused_rooms[room_id] = True
        logger.info(f"[AgentLoop] Room {room_id} pause requested")
    
    def is_paused(self, room_id: str) -> bool:
        return self._paused_rooms.get(room_id, False)
    
    def clear_pause(self, room_id: str):
        self._paused_rooms.pop(room_id, None)
    
    def submit_env_vars(self, room_id: str, values: dict) -> bool:
        """前端提交环境变量，唤醒等待的 agent loop"""
        waiter = self._env_var_waiters.get(room_id)
        if waiter:
            waiter["values"].update(values)
            waiter["event"].set()
            logger.info(f"[AgentLoop] Room {room_id} 环境变量已提交: {list(values.keys())}")
            return True
        logger.warning(f"[AgentLoop] Room {room_id} 没有等待环境变量的请求")
        return False
    
    async def _wait_for_env_vars(self, room_id: str, env_vars_info: dict, timeout: float = 300) -> dict:
        """等待前端提交环境变量，返回用户输入的值"""
        event = asyncio.Event()
        waiter = {"event": event, "values": {}}
        self._env_var_waiters[room_id] = waiter
        
        try:
            logger.info(f"[AgentLoop] Room {room_id} 等待环境变量输入: {list(env_vars_info.keys())}")
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return waiter["values"]
        except asyncio.TimeoutError:
            logger.warning(f"[AgentLoop] Room {room_id} 环境变量输入超时")
            return {}
        finally:
            self._env_var_waiters.pop(room_id, None)
    
    def _reload_user_messages(self, room_id: str, context: dict) -> list[dict]:
        """从数据库重新加载最新的用户消息，合并到 conversation_history"""
        try:
            db = SessionLocal()
            try:
                messages = db.query(Message).filter(
                    Message.room_id == room_id
                ).order_by(Message.id.asc()).all()
                
                history = []
                for msg in messages:
                    history.append({"role": msg.role, "content": msg.content})
                
                # 更新 context 中的 conversation_history
                context["conversation_history"] = history
                logger.info(f"[AgentLoop] Reloaded {len(history)} messages for room {room_id}")
                return history
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[AgentLoop] Failed to reload messages: {e}")
            return context.get("conversation_history", [])
    
    async def run_loop(
        self, 
        user_input: str, 
        context: Optional[dict] = None,
        max_iterations: int = 10,
        enabled_tools: Optional[list[str]] = None
    ) -> AsyncGenerator[str, None]:
        room_id = (context or {}).get("room_id", "")
        self.clear_pause(room_id)
        
        state = {
            "original_request": user_input,
            "context": context or {},
            "completed_steps": [],
            "current_results": {},
            "iteration": 0,
            "status": "running"
        }
        
        if enabled_tools is not None:
            state["context"]["enabled_tools"] = enabled_tools
        
        yield f"data: {json.dumps({'type': 'start', 'message': '开始处理任务'}, ensure_ascii=False)}\n\n"
        
        brain_result: dict = {}
        
        while state["iteration"] < max_iterations:
            # 检查暂停
            if self.is_paused(room_id):
                state["status"] = "paused"
                yield f"data: {json.dumps({'type': 'paused', 'message': '任务已暂停'}, ensure_ascii=False)}\n\n"
                return
            
            state["iteration"] += 1
            
            yield f"data: {json.dumps({'type': 'iteration', 'iteration': state['iteration']}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'agent_status', 'agent': 'brain', 'status': 'thinking'}, ensure_ascii=False)}\n\n"
            
            # 在 brain agent 前重新加载用户消息
            if room_id:
                self._reload_user_messages(room_id, state["context"])
            
            # 流式 Brain 分析
            # 获取最近一次 check agent 的反馈
            last_check = next((s for s in reversed(state["completed_steps"]) if s.get("agent") == "check"), None)
            
            if state["iteration"] == 1:
                brain_input = user_input
            elif last_check:
                feedback = last_check.get("result", {})
                check_feedback = {
                    "reason": feedback.get("reason", ""),
                    "missing_aspects": feedback.get("missing_aspects", []),
                    "suggestions": feedback.get("suggestions", []),
                }
                brain_input = (
                    f"原始请求: {user_input}\n\n"
                    f"上轮检查反馈（任务尚未完成，请根据以下反馈继续）:\n"
                    f"{json.dumps(check_feedback, ensure_ascii=False)}\n\n"
                    f"已完成步骤摘要:\n"
                    f"{json.dumps(state['completed_steps'], ensure_ascii=False)}"
                )
            else:
                brain_input = f"基于之前的执行结果，继续处理任务。已完成步骤: {json.dumps(state['completed_steps'], ensure_ascii=False)}"
            
            # 各 agent（brain/task/check）内部自行保存消息到数据库，agent_loop 无需重复保存
            async for event_type, event_data in self.brain.analyze_intent_stream(brain_input, state["context"]):
                # 检查暂停
                if self.is_paused(room_id):
                    state["status"] = "paused"
                    yield f"data: {json.dumps({'type': 'paused', 'message': '任务已暂停'}, ensure_ascii=False)}\n\n"
                    return
                
                if event_type == "chunk":
                    yield f"data: {json.dumps({'type': 'brain_stream', 'content': event_data}, ensure_ascii=False)}\n\n"
                elif event_type == "tool_args":
                    yield f"data: {json.dumps({'type': 'brain_stream', 'content': event_data}, ensure_ascii=False)}\n\n"
                elif event_type == "result":
                    brain_result = event_data
                elif event_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event_data.get('error', 'Unknown error')}, ensure_ascii=False)}\n\n"
                    return
            
            yield f"data: {json.dumps({'type': 'brain_result', 'data': brain_result}, ensure_ascii=False)}\n\n"
            
            state["completed_steps"].append({
                "iteration": state["iteration"],
                "agent": "brain",
                "action": "analyze",
                "result": brain_result
            })
            
            next_action = brain_result.get("next_action", "continue")
            tasks = brain_result.get("tasks", [])
            
            logger.info(f"[AgentLoop] Brain result - next_action: {next_action}, tasks count: {len(tasks)}")
            logger.info(f"[AgentLoop] Tasks: {json.dumps(tasks, ensure_ascii=False)[:500]}")
            logger.info(f"[AgentLoop] is_complete: {brain_result.get('is_complete')}")
            
            if tasks and len(tasks) > 0:
                current_task = tasks[0]
                task_type = current_task.get("type", "tool_call")
                
                logger.info(f"[AgentLoop] Executing task - type: {task_type}, task: {json.dumps(current_task, ensure_ascii=False)[:300]}")
                
                ctx = state.get("context", {})
                variable_service: Optional[VariableService] = ctx.get("variable_service")
                room_id = ctx.get("room_id", "")
                
                yield f"data: {json.dumps({'type': 'agent_status', 'agent': 'task', 'status': 'working', 'task': current_task}, ensure_ascii=False)}\n\n"
                
                if task_type == "tool_call":
                    tool_name = current_task.get("tool")
                    params = current_task.get("params", {})
                    
                    if variable_service:
                        params = variable_service.resolve_dict_variables(room_id, params)
                    
                    task_input = {"tool": tool_name, "params": params}
                    task_result = await self.task.execute_task("tool_call", task_input, state["context"])

                    if not task_result.get("e"):
                        file_created = task_result.get("d", {}).get("output", {}).get("file_created")
                        if file_created:
                            yield f"data: {json.dumps({'type': 'file_created', 'data': file_created}, ensure_ascii=False)}\n\n"
                elif task_type == "file_operation":
                    operation = current_task.get("operation")
                    params = current_task.get("params", {})
                    
                    if variable_service:
                        params = variable_service.resolve_dict_variables(room_id, params)
                    
                    task_input = {
                        "operation": operation,
                        "params": params
                    }
                    task_result = await self.task.execute_task("file_operation", task_input, state["context"])
                    
                    if not task_result.get("e") and operation in ["file_write", "write"]:
                        yield f"data: {json.dumps({'type': 'file_created', 'data': task_result.get('d')}, ensure_ascii=False)}\n\n"
                elif task_type == "llm_generate":
                    params = current_task.get("params", {})
                    
                    logger.info(f"[AgentLoop] LLM generate task - params: {json.dumps(params, ensure_ascii=False)[:200]}")
                    
                    if variable_service:
                        params = variable_service.resolve_dict_variables(room_id, params)
                        logger.info(f"[AgentLoop] Variables resolved in params")
                    
                    task_input = {"params": params}
                    
                    logger.info(f"[AgentLoop] Calling execute_task_stream for llm_generate")
                    
                    task_result = {}
                    chunk_count = 0
                    async for chunk in self.task.execute_task_stream("llm_generate", task_input, state["context"]):
                        # 检查暂停
                        if self.is_paused(room_id):
                            state["status"] = "paused"
                            yield f"data: {json.dumps({'type': 'paused', 'message': '任务已暂停'}, ensure_ascii=False)}\n\n"
                            return
                        
                        chunk_count += 1
                        if chunk_count <= 3:
                            logger.info(f"[AgentLoop] Received chunk {chunk_count}: {chunk[:100]}")
                        
                        try:
                            resp = json.loads(chunk)
                            # 检查是否有错误 (e 字段)
                            if resp.get("e"):
                                task_result = {"e": resp.get("e"), "m": resp.get("m"), "d": None}
                                logger.error(f"[AgentLoop] LLM generate error: {resp.get('m')}")
                                continue
                            
                            data = resp.get("d", {})
                            if data.get("type") == "content":
                                yield f"data: {json.dumps({'type': 'llm_generate_stream', 'content': data.get('content')}, ensure_ascii=False)}\n\n"
                            elif data.get("type") == "complete":
                                task_result = resp
                                variable_name = data.get("variable_name", "")
                                content_length = data.get("content_length", 0)
                                logger.info(f"[AgentLoop] LLM generate complete: variable={variable_name}, length={content_length}")
                                yield f"data: {json.dumps({'type': 'variable_set', 'data': {'variable_name': variable_name}}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            logger.warning(f"[AgentLoop] Failed to parse chunk: {chunk[:100]}")
                    
                    logger.info(f"[AgentLoop] Total chunks received: {chunk_count}")
                elif task_type == "variable_operation":
                    params = current_task.get("params", {})
                    operation = current_task.get("operation") or params.pop("operation", None)
                    
                    if variable_service:
                        params = variable_service.resolve_dict_variables(room_id, params)
                    
                    task_input = {
                        "operation": operation,
                        "params": params
                    }
                    task_result = await self.task.execute_task("variable_operation", task_input, state["context"])
                    
                    if not task_result.get("e") and operation == "set_variable":
                        yield f"data: {json.dumps({'type': 'variable_set', 'data': task_result.get('d')}, ensure_ascii=False)}\n\n"
                elif task_type == "image_operation":
                    operation = current_task.get("operation")
                    params = current_task.get("params", {})
                    
                    logger.info(f"[AgentLoop] Image operation task - operation: {operation}, params: {json.dumps(params, ensure_ascii=False)[:200]}")
                    
                    if variable_service:
                        params = variable_service.resolve_dict_variables(room_id, params)
                        logger.info(f"[AgentLoop] Variables resolved in params")
                    
                    task_input = {
                        "operation": operation,
                        "params": params
                    }
                    
                    logger.info(f"[AgentLoop] Calling execute_task_stream for image_operation")
                    
                    task_result = {}
                    chunk_count = 0
                    async for chunk in self.task.execute_task_stream("image_operation", task_input, state["context"]):
                        if self.is_paused(room_id):
                            state["status"] = "paused"
                            yield f"data: {json.dumps({'type': 'paused', 'message': '任务已暂停'}, ensure_ascii=False)}\n\n"
                            return
                        
                        chunk_count += 1
                        if chunk_count <= 3:
                            logger.info(f"[AgentLoop] Received image chunk {chunk_count}: {chunk[:100]}")
                        
                        try:
                            resp = json.loads(chunk)
                            if resp.get("e"):
                                task_result = {"e": resp.get("e"), "m": resp.get("m"), "d": None}
                                logger.error(f"[AgentLoop] Image operation error: {resp.get('m')}")
                                continue
                            
                            data = resp.get("d", {})
                            if data.get("type") == "content":
                                yield f"data: {json.dumps({'type': 'image_understand_stream', 'content': data.get('content')}, ensure_ascii=False)}\n\n"
                            elif data.get("type") == "complete":
                                task_result = resp
                                variable_name = data.get("variable_name", "")
                                content_length = data.get("content_length", 0)
                                images = data.get("images", [])
                                logger.info(f"[AgentLoop] Image operation complete: variable={variable_name}, length={content_length}, images={len(images)}")
                                if variable_name:
                                    yield f"data: {json.dumps({'type': 'variable_set', 'data': {'variable_name': variable_name}}, ensure_ascii=False)}\n\n"
                                if images:
                                    for img in images:
                                        yield f"data: {json.dumps({'type': 'file_created', 'data': img}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            logger.warning(f"[AgentLoop] Failed to parse image chunk: {chunk[:100]}")
                    
                    logger.info(f"[AgentLoop] Total image chunks received: {chunk_count}")
                else:
                    task_result = await self.task.execute_task(
                        task_type,
                        current_task.get("description", user_input),
                        state["context"]
                    )
                
                yield f"data: {json.dumps({'type': 'task_result', 'data': task_result}, ensure_ascii=False)}\n\n"
                
                state["completed_steps"].append({
                    "iteration": state["iteration"],
                    "agent": "task",
                    "action": task_type,
                    "result": task_result
                })
                
                state["current_results"][f"iteration_{state['iteration']}"] = task_result
                
                # 检查暂停
                if self.is_paused(room_id):
                    state["status"] = "paused"
                    yield f"data: {json.dumps({'type': 'paused', 'message': '任务已暂停'}, ensure_ascii=False)}\n\n"
                    return
                
                # 在 check agent 前重新加载用户消息
                if room_id:
                    self._reload_user_messages(room_id, state["context"])
                
                yield f"data: {json.dumps({'type': 'agent_status', 'agent': 'check', 'status': 'checking'}, ensure_ascii=False)}\n\n"
                
                check_result: dict = {}
                async for event_type, event_data in self.check.check_task_completion_stream(
                    user_input,
                    task_result,
                    state["completed_steps"],
                    state["context"]
                ):
                    # 检查暂停
                    if self.is_paused(room_id):
                        state["status"] = "paused"
                        yield f"data: {json.dumps({'type': 'paused', 'message': '任务已暂停'}, ensure_ascii=False)}\n\n"
                        return
                    
                    if event_type == "chunk":
                        yield f"data: {json.dumps({'type': 'check_stream', 'content': event_data}, ensure_ascii=False)}\n\n"
                    elif event_type == "tool_args":
                        yield f"data: {json.dumps({'type': 'check_stream', 'content': event_data}, ensure_ascii=False)}\n\n"
                    elif event_type == "result":
                        check_result = event_data
                    elif event_type == "error":
                        yield f"data: {json.dumps({'type': 'error', 'message': event_data.get('error', 'Unknown error')}, ensure_ascii=False)}\n\n"
                        return
                
                yield f"data: {json.dumps({'type': 'check_result', 'data': check_result}, ensure_ascii=False)}\n\n"
                
                state["completed_steps"].append({
                    "iteration": state["iteration"],
                    "agent": "check",
                    "action": "check",
                    "result": check_result
                })
                
                if check_result.get("is_complete", False):
                    state["status"] = "completed"
                    summary = (
                        check_result.get("response_to_user") or 
                        check_result.get("summary") or 
                        brain_result.get("response_to_user") or 
                        "任务已完成"
                    )
                    yield f"data: {json.dumps({'type': 'summary', 'content': summary}, ensure_ascii=False)}\n\n"
                    break
            
            elif brain_result.get("is_complete", False):
                state["status"] = "completed"
                summary = brain_result.get("response_to_user", "任务已完成")
                yield f"data: {json.dumps({'type': 'summary', 'content': summary}, ensure_ascii=False)}\n\n"
                break
            
            else:
                yield f"data: {json.dumps({'type': 'info', 'message': '没有待执行的任务'}, ensure_ascii=False)}\n\n"
                state["status"] = "completed"
                break
        
        if state["iteration"] >= max_iterations:
            yield f"data: {json.dumps({'type': 'warning', 'message': f'达到最大迭代次数 {max_iterations}'}, ensure_ascii=False)}\n\n"
            summary = brain_result.get("response_to_user", "任务已完成（达到最大迭代次数）")
            yield f"data: {json.dumps({'type': 'summary', 'content': summary}, ensure_ascii=False)}\n\n"
        
        yield f"data: {json.dumps({'type': 'done', 'status': state['status'], 'iterations': state['iteration']}, ensure_ascii=False)}\n\n"


orchestrator = AgentLoopOrchestrator()


async def _prepare_context(context: Optional[dict], user_id: int, room_id: str, db, user_input: str) -> dict:
    if not context:
        context = {}
    
    context["user_id"] = user_id
    context["room_id"] = room_id
    
    variable_service = VariableService(db)
    context["variable_service"] = variable_service
    
    room = db.query(Room).filter(Room.id == room_id, Room.user_id == user_id).first()
    room_models = room.models if room and room.models else {}
    
    config_id = context.get("config_id")
    if config_id:
        try:
            config, api_key = get_config_api_key(config_id, user_id, db)
            request_url = get_default_url(config.provider, config.call_method, config.category, config.sub_category)
            if config.base_url:
                request_url = build_request_url(config.base_url, config.call_method)
            context["api_key"] = api_key
            context["api_url"] = request_url
            context["model"] = config.model_name
            context["call_method"] = config.call_method
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    vision_config_id = None
    if isinstance(room_models.get("vision"), dict):
        vision_config_id = room_models["vision"].get("image_understanding")
    elif isinstance(room_models.get("vision_image_understanding"), (int, str)):
        vision_config_id = room_models.get("vision_image_understanding")
    
    if not vision_config_id:
        from app.models import ModelConfig
        default_vision_config = db.query(ModelConfig).filter(
            ModelConfig.user_id == user_id,
            ModelConfig.category == "vision",
            ModelConfig.sub_category == "image_understanding",
            ModelConfig.is_default == True
        ).first()
        if default_vision_config:
            vision_config_id = default_vision_config.id
        else:
            first_vision_config = db.query(ModelConfig).filter(
                ModelConfig.user_id == user_id,
                ModelConfig.category == "vision",
                ModelConfig.sub_category == "image_understanding"
            ).first()
            if first_vision_config:
                vision_config_id = first_vision_config.id
    
    if vision_config_id:
        try:
            vision_config_id = int(vision_config_id)
            vision_config, vision_api_key = get_config_api_key(vision_config_id, user_id, db)
            vision_url = get_default_url(vision_config.provider, vision_config.call_method, vision_config.category, vision_config.sub_category)
            if vision_config.base_url:
                vision_url = build_request_url(vision_config.base_url, vision_config.call_method)
            context["vision_api_key"] = vision_api_key
            context["vision_api_url"] = vision_url
            context["vision_model"] = vision_config.model_name
            context["vision_call_method"] = vision_config.call_method
            context["vision_config_id"] = vision_config_id
        except ValueError as e:
            logger.warning(f"[AgentLoop] Failed to load vision config: {e}")
    
    image_gen_config_id = None
    if isinstance(room_models.get("vision"), dict):
        image_gen_config_id = room_models["vision"].get("image_generation")
    elif isinstance(room_models.get("vision_image_generation"), (int, str)):
        image_gen_config_id = room_models.get("vision_image_generation")
    
    if not image_gen_config_id:
        from app.models import ModelConfig
        default_image_gen_config = db.query(ModelConfig).filter(
            ModelConfig.user_id == user_id,
            ModelConfig.category == "vision",
            ModelConfig.sub_category == "image_generation",
            ModelConfig.is_default == True
        ).first()
        if default_image_gen_config:
            image_gen_config_id = default_image_gen_config.id
        else:
            first_image_gen_config = db.query(ModelConfig).filter(
                ModelConfig.user_id == user_id,
                ModelConfig.category == "vision",
                ModelConfig.sub_category == "image_generation"
            ).first()
            if first_image_gen_config:
                image_gen_config_id = first_image_gen_config.id
    
    if image_gen_config_id:
        try:
            image_gen_config_id = int(image_gen_config_id)
            image_gen_config, image_gen_api_key = get_config_api_key(image_gen_config_id, user_id, db)
            image_gen_url = get_default_url(image_gen_config.provider, image_gen_config.call_method, image_gen_config.category, image_gen_config.sub_category)
            if image_gen_config.base_url:
                image_gen_url = build_request_url(image_gen_config.base_url, image_gen_config.call_method)
            context["image_gen_api_key"] = image_gen_api_key
            context["image_gen_api_url"] = image_gen_url
            context["image_gen_model"] = image_gen_config.model_name
            context["image_gen_call_method"] = image_gen_config.call_method
            context["image_gen_config_id"] = image_gen_config_id
        except ValueError as e:
            logger.warning(f"[AgentLoop] Failed to load image generation config: {e}")
    
    context_service = ContextService(db)
    full_context = await context_service.build_context(
        user_id=user_id,
        room_id=room_id,
        current_input=user_input,
        base_context=context
    )
    
    return full_context


@router.post("/run")
async def run_agent_loop(
    request: LoopRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    context = await _prepare_context(request.context, current_user.id, request.room_id, db, request.user_input)
    
    return StreamingResponse(
        orchestrator.run_loop(
            user_input=request.user_input,
            context=context,
            max_iterations=request.max_iterations,
            enabled_tools=request.enabled_tools
        ),
        media_type="text/event-stream"
    )


@router.post("/run-sync")
async def run_agent_loop_sync(
    request: LoopRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    context = await _prepare_context(request.context, current_user.id, request.room_id, db, request.user_input)
    
    results = []
    final_summary = ""
    
    async for event in orchestrator.run_loop(
        user_input=request.user_input,
        context=context,
        max_iterations=request.max_iterations,
        enabled_tools=request.enabled_tools
    ):
        if event.startswith("data: "):
            data = json.loads(event[6:])
            results.append(data)
            if data.get("type") == "summary":
                final_summary = data.get("content", "")
    
    return success({
        "summary": final_summary,
        "steps": results,
        "total_steps": len(results)
    })


@router.get("/tools")
def get_available_tools(
    current_user: User = Depends(get_current_user),
):
    return success(tool_registry.get_all_schemas())


class PauseRequest(BaseModel):
    room_id: str


class EnvVarsRequest(BaseModel):
    room_id: str
    values: dict


@router.post("/pause")
def pause_agent_loop(
    request: PauseRequest,
    current_user: User = Depends(get_current_user),
):
    orchestrator.pause_room(request.room_id)
    return success(message="暂停请求已发送")


@router.post("/submit-env-vars")
def submit_env_vars(
    request: EnvVarsRequest,
    current_user: User = Depends(get_current_user),
):
    ok = orchestrator.submit_env_vars(request.room_id, request.values)
    if ok:
        return success(message="环境变量已提交")
    else:
        return success(message="没有等待环境变量的请求")



