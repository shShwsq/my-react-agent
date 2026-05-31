import json
import logging
from typing import Any, Optional, Callable, AsyncGenerator, Union
from app.agents.base import BaseAgent, AgentType, AgentTask, AgentStatus
from app.services.text_service import TextService
from app.tasks.tools import tool_registry
from app.tasks.file_operations import file_operation_registry
from app.tasks.variable_operations import variable_operation_registry
from app.tasks.llm_generate import llm_generate_registry
from app.tasks.image_operations import image_operation_registry
from app.schemas import ApiResponse, TaskErrorCode
from app.database import SessionLocal
from app.models import Message

logger = logging.getLogger(__name__)


def task_success(data: Any = None, message: str = "") -> dict:
    """构建任务执行成功的响应"""
    return ApiResponse(e="", d=data, m=message).model_dump()


def task_fail(error: TaskErrorCode = TaskErrorCode.INTERNAL_ERROR, data: Any = None, message: str = "") -> dict:
    """构建任务执行失败的响应"""
    err_msg = message if message else error.default_msg
    return ApiResponse(e=error.value, d=data, m=err_msg).model_dump()


class TaskAgent(BaseAgent):
    def __init__(self, agent_id: str = "task-001"):
        super().__init__(agent_id, AgentType.TASK)
        self.text_service = TextService()
        self.task_handlers: dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        self.task_handlers = {
            "tool_call": self._handle_tool_call,
            "file_operation": self._handle_file_operation,
            "variable_operation": self._handle_variable_operation,
            "llm_generate": self._handle_llm_generate,
            "image_operation": self._handle_image_operation,
        }

    def register_handler(self, task_type: str, handler: Callable):
        self.task_handlers[task_type] = handler

    async def _handle_file_operation(self, input_data: Any, context: dict) -> dict:
        operation_name = input_data.get("operation") if isinstance(input_data, dict) else None
        params = input_data.get("params", {}) if isinstance(input_data, dict) else {}
        
        if not operation_name:
            return task_fail(
                error=TaskErrorCode.TASK_CONFIG_ERROR,
                data={"available_operations": file_operation_registry.list_operations()},
                message="未指定文件操作类型"
            )
        
        operation = file_operation_registry.get(operation_name)
        if not operation:
            return task_fail(
                error=TaskErrorCode.FILE_OP_NOT_FOUND,
                data={"available_operations": file_operation_registry.list_operations()},
                message=f"文件操作 '{operation_name}' 不存在"
            )
        
        try:
            merged_params = {**params, **context}
            result = await operation.execute(**merged_params)
            if result.success:
                output_dict = result.output if isinstance(result.output, dict) else {}
                return task_success(
                    data={
                        "operation": operation_name,
                        **output_dict,
                    },
                    message=f"文件操作 {operation_name} 执行成功"
                )
            else:
                return task_fail(
                    error=TaskErrorCode.FILE_OP_ERROR,
                    data={"operation": operation_name},
                    message=result.error or "文件操作失败"
                )
        except Exception as e:
            logger.error(f"[TaskAgent] File operation error: {e}")
            return task_fail(
                error=TaskErrorCode.FILE_OP_ERROR,
                data={"operation": operation_name},
                message=str(e)
            )

    async def _handle_tool_call(self, input_data: Any, context: dict) -> dict:
        tool_name = input_data.get("tool") if isinstance(input_data, dict) else None
        params = input_data.get("params", {}) if isinstance(input_data, dict) else {}
        
        if not tool_name:
            return task_fail(error=TaskErrorCode.TASK_CONFIG_ERROR, message="未指定工具名称")
        
        tool = tool_registry.get(tool_name)
        if not tool:
            return task_fail(
                error=TaskErrorCode.TOOL_NOT_FOUND,
                data={"available_tools": tool_registry.list_tools()},
                message=f"工具 '{tool_name}' 不存在"
            )
        
        enabled_tools = context.get("enabled_tools")
        if enabled_tools is not None and tool_name not in enabled_tools:
            return task_fail(
                error=TaskErrorCode.TOOL_NOT_FOUND,
                message=f"工具 '{tool_name}' 已被禁用，请在设置中启用"
            )
        
        try:
            merged_params = {**params, **context}
            result = await tool.execute(**merged_params)
            if result.success:
                return task_success(
                    data={"output": result.output, "metadata": result.metadata, "tool": tool_name},
                    message=f"工具 {tool_name} 执行成功"
                )
            else:
                error_msg = result.error or "工具执行失败"
                logger.error(
                    f"[TaskAgent] Tool {tool_name} 执行失败 | error={result.error!r} "
                    f"fallback_message={error_msg}"
                )
                return task_fail(
                    error=TaskErrorCode.TOOL_EXECUTION_ERROR,
                    data={"tool": tool_name},
                    message=error_msg
                )
        except Exception as e:
            logger.error(f"[TaskAgent] Tool execution error: {e}")
            return task_fail(
                error=TaskErrorCode.TOOL_EXECUTION_ERROR,
                data={"tool": tool_name},
                message=str(e)
            )

    async def _handle_variable_operation(self, input_data: Any, context: dict) -> dict:
        operation_name = input_data.get("operation") if isinstance(input_data, dict) else None
        params = input_data.get("params", {}) if isinstance(input_data, dict) else {}
        
        if not operation_name:
            return task_fail(
                error=TaskErrorCode.TASK_CONFIG_ERROR,
                data={"available_operations": variable_operation_registry.list_operations()},
                message="未指定变量操作类型"
            )
        
        operation = variable_operation_registry.get(operation_name)
        if not operation:
            return task_fail(
                error=TaskErrorCode.VAR_OP_NOT_FOUND,
                data={"available_operations": variable_operation_registry.list_operations()}
            )
        
        try:
            merged_params = {**params, **context}
            result = await operation.execute(**merged_params)
            if result.success:
                return task_success(
                    data={"output": result.output, "operation": operation_name},
                    message=f"变量操作 {operation_name} 执行成功"
                )
            else:
                return task_fail(
                    error=TaskErrorCode.VAR_OP_ERROR,
                    data={"operation": operation_name},
                    message=result.error or "变量操作失败"
                )
        except Exception as e:
            logger.error(f"[TaskAgent] Variable operation error: {e}")
            return task_fail(
                error=TaskErrorCode.VAR_OP_ERROR,
                data={"operation": operation_name},
                message=str(e)
            )

    async def _handle_llm_generate(self, input_data: Any, context: dict):
        params = input_data.get("params", {}) if isinstance(input_data, dict) else {}
        
        logger.info(f"[TaskAgent] _handle_llm_generate called with params: {json.dumps(params, ensure_ascii=False)[:200]}")
        logger.info(f"[TaskAgent] Context keys: {list(context.keys()) if context else 'None'}")
        
        generator = llm_generate_registry.get("content_generator")
        if not generator:
            logger.error(f"[TaskAgent] LLM generator not found in registry")
            error_resp = task_fail(error=TaskErrorCode.LLM_GEN_NOT_FOUND, message="LLM 生成器不存在")
            yield json.dumps({"type": "error", "error": error_resp}, ensure_ascii=False)
            return
        
        logger.info(f"[TaskAgent] Generator found, starting execution")
        
        try:
            merged_params = {**params, **context}
            logger.info(f"[TaskAgent] Merged params keys: {list(merged_params.keys())}")
            
            chunk_count = 0
            async for chunk in generator.execute(**merged_params):
                chunk_count += 1
                if chunk_count <= 3:
                    logger.info(f"[TaskAgent] Chunk {chunk_count}: {chunk[:100]}")
                yield chunk
            
            logger.info(f"[TaskAgent] Total chunks generated: {chunk_count}")
        except Exception as e:
            logger.error(f"[TaskAgent] LLM generate error: {e}", exc_info=True)
            error_resp = task_fail(error=TaskErrorCode.LLM_GENERATION_ERROR, message=str(e))
            yield json.dumps({"type": "error", "error": error_resp}, ensure_ascii=False)

    async def _handle_image_operation(self, input_data: Any, context: dict):
        operation_name = input_data.get("operation") if isinstance(input_data, dict) else None
        params = input_data.get("params", {}) if isinstance(input_data, dict) else {}
        
        logger.info(f"[TaskAgent] _handle_image_operation called - operation: {operation_name}")
        logger.info(f"[TaskAgent] Params: {json.dumps(params, ensure_ascii=False)[:200]}")
        
        if not operation_name:
            error_resp = task_fail(
                error=TaskErrorCode.TASK_CONFIG_ERROR,
                data={"available_operations": image_operation_registry.list_operations()},
                message="未指定图片操作类型"
            )
            yield json.dumps({"type": "error", "error": error_resp}, ensure_ascii=False)
            return
        
        operation = image_operation_registry.get(operation_name)
        if not operation:
            error_resp = task_fail(
                error=TaskErrorCode.FILE_OP_NOT_FOUND,
                data={"available_operations": image_operation_registry.list_operations()},
                message=f"图片操作 '{operation_name}' 不存在"
            )
            yield json.dumps({"type": "error", "error": error_resp}, ensure_ascii=False)
            return
        
        try:
            merged_params = {**params, **context}
            logger.info(f"[TaskAgent] Merged params keys: {list(merged_params.keys())}")
            
            chunk_count = 0
            async for chunk in operation.execute(**merged_params):
                chunk_count += 1
                if chunk_count <= 3:
                    logger.info(f"[TaskAgent] Image chunk {chunk_count}: {chunk[:100]}")
                yield chunk
            
            logger.info(f"[TaskAgent] Total image chunks generated: {chunk_count}")
        except Exception as e:
            logger.error(f"[TaskAgent] Image operation error: {e}", exc_info=True)
            error_resp = task_fail(error=TaskErrorCode.FILE_OP_ERROR, message=str(e))
            yield json.dumps({"type": "error", "error": error_resp}, ensure_ascii=False)

    async def execute_task(self, task_type: str, input_data: Any, context: Optional[dict] = None) -> dict:
        handler = self.task_handlers.get(task_type)
        
        if not handler:
            logger.warning(f"[TaskAgent] No handler for task type: {task_type}")
            return task_fail(error=TaskErrorCode.TASK_TYPE_INVALID, message=f"不支持的任务类型: {task_type}")
        
        result = await handler(input_data, context or {})
        
        # 保存执行结果到数据库
        room_id = context.get("room_id", "") if context else ""
        if room_id:
            try:
                db = SessionLocal()
                msg = Message(room_id=room_id, role="task", content=json.dumps(result, ensure_ascii=False))
                db.add(msg)
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"[TaskAgent] Failed to save result: {e}")
        
        return result
    
    def is_streaming_task(self, task_type: str) -> bool:
        return task_type in ["llm_generate", "image_operation"]
    
    async def execute_task_stream(self, task_type: str, input_data: Any, context: Optional[dict] = None):
        logger.info(f"[TaskAgent] execute_task_stream called - task_type: {task_type}")
        logger.info(f"[TaskAgent] is_streaming_task: {self.is_streaming_task(task_type)}")
        
        if not self.is_streaming_task(task_type):
            logger.info(f"[TaskAgent] Non-streaming task, executing normally")
            result = await self.execute_task(task_type, input_data, context)
            yield json.dumps({"type": "result", "data": result}, ensure_ascii=False)
            return
        
        handler = self.task_handlers.get(task_type)
        if not handler:
            error_resp = task_fail(error=TaskErrorCode.TASK_TYPE_INVALID, message=f"不支持的任务类型: {task_type}")
            yield json.dumps({"type": "error", "error": error_resp}, ensure_ascii=False)
            return
        
        final_result = None
        async for chunk in handler(input_data, context or {}):
            # 跟踪最终结果用于保存
            try:
                resp = json.loads(chunk)
                if resp.get("d", {}).get("type") == "complete":
                    final_result = resp
            except (json.JSONDecodeError, TypeError):
                pass
            yield chunk
        
        # 保存流式任务的最终结果到数据库
        if final_result:
            room_id = context.get("room_id", "") if context else ""
            if room_id:
                try:
                    db = SessionLocal()
                    msg = Message(room_id=room_id, role="task", content=json.dumps(final_result, ensure_ascii=False))
                    db.add(msg)
                    db.commit()
                    db.close()
                except Exception as e:
                    logger.error(f"[TaskAgent] Failed to save streaming result: {e}")

    async def execute_tool(self, tool_name: str, params: dict) -> dict:
        tool = tool_registry.get(tool_name)
        if not tool:
            return task_fail(
                error=TaskErrorCode.TOOL_NOT_FOUND,
                message=f"工具 '{tool_name}' 不存在"
            )
        
        try:
            result = await tool.execute(**params)
            if result.success:
                return task_success(data={"output": result.output}, message=f"工具 {tool_name} 执行成功")
            else:
                return task_fail(
                    error=TaskErrorCode.TOOL_EXECUTION_ERROR,
                    message=result.error or "工具执行失败"
                )
        except Exception as e:
            logger.error(f"[TaskAgent] Tool execution error: {e}")
            return task_fail(
                error=TaskErrorCode.TOOL_EXECUTION_ERROR,
                message=str(e)
            )

    async def process(self, task: AgentTask) -> AgentTask:
        self.update_status(AgentStatus.WORKING)
        self.add_message("system", f"开始执行任务: {task.task_id}")
        
        try:
            task_type = task.task_type or "tool_call"
            context = task.metadata or {}
            
            result = await self.execute_task(task_type, task.input_data, context)
            
            task.result = result
            task.status = "completed"
            
            self.update_status(AgentStatus.COMPLETED)
            self.add_message("assistant", f"任务执行完成: {task.task_id}")
            
        except Exception as e:
            logger.error(f"[TaskAgent] Error processing task: {e}")
            task.status = "error"
            task.error = str(e)
            self.update_status(AgentStatus.ERROR)
            self.add_message("system", f"任务执行错误: {str(e)}")
        
        return task

    def get_capabilities(self) -> list[str]:
        return list(self.task_handlers.keys())
