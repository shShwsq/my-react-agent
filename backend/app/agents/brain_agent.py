import json
import logging
import re
from typing import Any, Optional
from app.agents.base import BaseAgent, AgentType, AgentTask, AgentStatus
from app.services.text_service import TextService
from app.tasks.tools import tool_registry
from app.tasks.file_operations import file_operation_registry
from app.tasks.variable_operations import variable_operation_registry
from app.tasks.llm_generate import llm_generate_registry
from app.tasks.image_operations import image_operation_registry
from app.utils.json_parser import parse_llm_json, parse_llm_tasks
from app.database import SessionLocal
from app.models import Message

logger = logging.getLogger(__name__)


class BrainAgent(BaseAgent):
    def __init__(self, agent_id: str = "brain-001"):
        super().__init__(agent_id, AgentType.BRAIN)
        self.text_service = TextService()
        self.sub_agents: dict[str, str] = {}
        self.conversation_history: list[dict] = []
        self.task_context: dict = {}

    def register_sub_agent(self, agent_type: str, agent_id: str):
        self.sub_agents[agent_type] = agent_id

    def _get_tools_schema(self) -> list[dict]:
        return [{
            "type": "function",
            "function": {
                "name": "decide_action",
                "description": "分析用户意图并决定下一步行动",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought": {
                            "type": "string",
                            "description": "你的思考过程"
                        },
                        "intent": {
                            "type": "string",
                            "description": "用户意图描述"
                        },
                        "next_action": {
                            "type": "string",
                            "enum": ["tool_call", "file_operation", "llm_generate", "variable_operation", "image_operation", "complete", "continue"],
                            "description": "下一步行动"
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["tool_call", "file_operation", "variable_operation", "llm_generate", "image_operation"]
                                    },
                                    "tool": {
                                        "type": "string",
                                        "description": "工具名称（type为tool_call时必填）"
                                    },
                                    "operation": {
                                        "type": "string",
                                        "description": "操作名称（type为file_operation或variable_operation或image_operation时必填）"
                                    },
                                    "params": {
                                        "type": "object",
                                        "description": "参数"
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "调用原因"
                                    }
                                },
                                "required": ["type", "params", "reason"]
                            },
                            "description": "任务列表，每次只返回一个任务"
                        },
                        "is_complete": {
                            "type": "boolean",
                            "description": "任务是否完成"
                        },
                        "response_to_user": {
                            "type": "string",
                            "description": "给用户的回复消息，必须填写"
                        }
                    },
                    "required": ["thought", "intent", "next_action", "tasks", "is_complete", "response_to_user"]
                }
            }
        }]

    def _build_system_prompt(self, enabled_tools: Optional[list[str]] = None) -> str:
        all_tool_schemas = tool_registry.get_all_schemas()
        
        if enabled_tools is not None:
            filtered_schemas = [s for s in all_tool_schemas if s['name'] in enabled_tools]
        else:
            filtered_schemas = all_tool_schemas
        
        tools_info = "\n".join([
            f"- {schema['name']}: {schema['description']}"
            for schema in filtered_schemas
        ])
        
        tools_params = "\n\n".join([
            f"工具: {schema['name']}\n参数: {json.dumps(schema['parameters'], ensure_ascii=False, indent=2)}"
            for schema in filtered_schemas
        ])
        
        file_ops_info = "\n".join([
            f"- {schema['name']}: {schema['description']}"
            for schema in file_operation_registry.get_all_schemas()
        ])
        
        file_ops_params = "\n\n".join([
            f"文件操作: {schema['name']}\n参数: {json.dumps(schema['parameters'], ensure_ascii=False, indent=2)}"
            for schema in file_operation_registry.get_all_schemas()
        ])
        
        var_ops_info = "\n".join([
            f"- {schema['name']}: {schema['description']}"
            for schema in variable_operation_registry.get_all_schemas()
        ])
        
        var_ops_params = "\n\n".join([
            f"变量操作: {schema['name']}\n参数: {json.dumps(schema['parameters'], ensure_ascii=False, indent=2)}"
            for schema in variable_operation_registry.get_all_schemas()
        ])
        
        llm_gen_info = "\n".join([
            f"- {schema['name']}: {schema['description']}"
            for schema in llm_generate_registry.get_all_schemas()
        ])
        
        llm_gen_params = "\n\n".join([
            f"LLM生成: {schema['name']}\n参数: {json.dumps(schema['parameters'], ensure_ascii=False, indent=2)}"
            for schema in llm_generate_registry.get_all_schemas()
        ])
        
        img_ops_info = "\n".join([
            f"- {schema['name']}: {schema['description']}"
            for schema in image_operation_registry.get_all_schemas()
        ])
        
        img_ops_params = "\n\n".join([
            f"图片操作: {schema['name']}\n参数: {json.dumps(schema['parameters'], ensure_ascii=False, indent=2)}"
            for schema in image_operation_registry.get_all_schemas()
        ])
        
        return f"""你是一个智能任务分析和协调助手。你的职责是：
1. 分析用户意图和需求
2. 将复杂任务分解为可执行的子任务
3. 决定下一步行动（调用工具、文件操作、LLM生成或完成任务）
4. 在任务完成后生成总结

可用工具：
{tools_info}

工具参数说明：
{tools_params}

文件操作：
{file_ops_info}

文件操作参数说明：
{file_ops_params}

变量操作：
{var_ops_info}

变量操作参数说明：
{var_ops_params}

LLM生成：
{llm_gen_info}

LLM生成参数说明：
{llm_gen_params}

图片操作：
{img_ops_info}

图片操作参数说明：
{img_ops_params}

变量引用（重要）：
- 格式：{{{{变量名}}}}
- 适用范围：params中的字符串值参数（如content、prompt、text等）
- 不适用：type、operation、filename、tool等固定参数
- 示例：{{"filename": "output.docx", "content": "{{{{article_content}}}}"}}
- 系统会自动替换为变量的实际值，无需先执行get_variable

任务类型说明：
- tool_call: 调用工具执行特定功能
- file_operation: 执行文件读写操作（适用于短内容，直接在 content 参数中提供）
- llm_generate: 调用大语言模型生成长内容（适用于需要生成大量文本的场景）
- image_operation: 图片操作，包含两个子操作：
  - image_understand: 理解图片内容并提取文字（支持上传的图片文件，流式输出）
  - image_generate: 根据文本描述生成图片并保存到文件
- variable_operation: 执行变量操作（设置、获取变量）

重要规则：
1. tasks 数组中每次只返回一个任务
2. 如果 tasks 数组有任务：
   - next_action 必须设置为任务的 type（"tool_call"、"file_operation"、"llm_generate"、"image_operation" 或 "variable_operation"）
   - is_complete 必须设置为 false
   - 任务将由 Task Agent 执行，执行后会再次询问你是否需要继续
3. 如果没有任务需要执行，且用户请求已满足：
   - 设置 is_complete 为 true
   - 设置 next_action 为 "complete"
4. 如果需要更多信息才能继续：
   - 设置 next_action 为 "continue"
   - 在回复内容中说明需要什么信息

JSON 格式要求（重要）：
1. tasks 必须是数组，不能是字符串
2. 如果参数内容很长，建议使用content_generate工具生成内容保存到变量中，然后通过变量引用格式引用该变量名
3. 确保 JSON 格式完整，不要截断

你可以直接回复用户消息，系统会自动处理你的决策。"""

    async def analyze_intent_stream(self, user_input: str, context: Optional[dict] = None):
        """流式分析意图，使用Function Calling获取结构化决策"""
        enabled_tools = context.get("enabled_tools") if context else None
        system_prompt = self._build_system_prompt(enabled_tools)
        if context and context.get("active_variables"):
            system_prompt += f"\n\n[当前可用变量]: {', '.join(context['active_variables'])}"
        
        # 历史对话：标准role直接追加，智能体role拼入system prompt
        agent_context_parts = []
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if context and context.get("conversation_history"):
            for msg in context["conversation_history"]:
                role = msg.get("role", "user")
                if role in ("user", "assistant"):
                    messages.append(msg)
                else:
                    agent_context_parts.append(f"[{role}]: {msg['content']}")
        
        if agent_context_parts:
            messages[0]["content"] += "\n\n## 历史决策记录\n" + "\n\n".join(agent_context_parts)
        
        messages.append({"role": "user", "content": user_input})
        
        full_content = ""
        tool_calls_data = []
        current_tool_args = ""
        try:
            async for chunk in self.text_service.stream_chat(
                messages=messages,
                model=context.get("model", "qwen-plus") if context else "qwen-plus",
                call_method=context.get("call_method", "chat") if context else "chat",
                api_key=context.get("api_key", "") if context else "",
                url=context.get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions") if context else "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                tools=self._get_tools_schema(),
                tool_choice={"type": "function", "function": {"name": "decide_action"}}
            ):
                if chunk.startswith("data: "):
                    data = chunk[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                        if "content" in parsed and parsed["content"]:
                            full_content += parsed["content"]
                            yield ("chunk", parsed["content"])
                        elif "tool_calls" in parsed:
                            for tc in parsed["tool_calls"]:
                                tool_calls_data.append(tc)
                                if "function" in tc and "arguments" in tc["function"]:
                                    args_delta = tc["function"]["arguments"]
                                    if args_delta:
                                        current_tool_args += args_delta
                                        yield ("tool_args", args_delta)
                        elif "error" in parsed:
                            yield ("error", {"error": parsed["error"]})
                            return
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"[BrainAgent] Final tool args: {current_tool_args[:500]}")
            
            if tool_calls_data:
                combined_args = ""
                for tc in tool_calls_data:
                    if "function" in tc and "arguments" in tc["function"]:
                        args = tc["function"]["arguments"]
                        if args:
                            combined_args += args
                
                logger.info(f"[BrainAgent] Combined tool arguments: {combined_args[:500]}")
                
                result = parse_llm_json(combined_args)
                
                if result and isinstance(result, dict):
                    logger.info(f"[BrainAgent] Parsed result: {json.dumps(result, ensure_ascii=False)[:500]}")
                    
                    if "tasks" in result:
                        original_tasks = result["tasks"]
                        logger.info(f"[BrainAgent] Original tasks type: {type(original_tasks)}, value: {str(original_tasks)[:200]}")
                        
                        parsed_tasks = parse_llm_tasks(result["tasks"])
                        result["tasks"] = parsed_tasks
                        
                        logger.info(f"[BrainAgent] Parsed tasks: {json.dumps(parsed_tasks, ensure_ascii=False)[:500]}")
                        logger.info(f"[BrainAgent] Tasks count: {len(parsed_tasks)}, is_complete: {result.get('is_complete')}, next_action: {result.get('next_action')}")
                else:
                    result = {
                        "thought": combined_args,
                        "intent": "待分析",
                        "response_to_user": "",
                        "tasks": [],
                        "next_action": "continue",
                        "is_complete": False
                    }
                    logger.warning(f"[BrainAgent] Failed to parse JSON, using fallback result")
            else:
                result = {
                    "thought": full_content,
                    "intent": "待分析",
                    "response_to_user": full_content,
                    "tasks": [],
                    "next_action": "continue",
                    "is_complete": False
                }
            
            if not result.get("response_to_user"):
                result["response_to_user"] = full_content if full_content else ""
            
            yield ("result", result)
            
            # 保存结果到数据库
            room_id = context.get("room_id", "") if context else ""
            if room_id:
                try:
                    db = SessionLocal()
                    msg = Message(room_id=room_id, role="brain", content=json.dumps(result, ensure_ascii=False))
                    db.add(msg)
                    db.commit()
                    db.close()
                except Exception as e:
                    logger.error(f"[BrainAgent] Failed to save result: {e}")
            
        except Exception as e:
            logger.error(f"[BrainAgent] Error in stream analyze: {e}")
            yield ("error", {"error": str(e)})

    async def analyze_intent(self, user_input: str, context: Optional[dict] = None) -> dict:
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_input}
        ]
        
        if context and context.get("history"):
            for msg in context["history"][-5:]:
                messages.insert(-1, msg)
        
        try:
            result = await self.text_service.chat(
                messages=messages,
                model=context.get("model", "qwen-plus") if context else "qwen-plus",
                call_method=context.get("call_method", "chat") if context else "chat",
                api_key=context.get("api_key", "") if context else "",
                url=context.get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions") if context else "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                tools=self._get_tools_schema(),
                tool_choice={"type": "function", "function": {"name": "decide_action"}}
            )
            
            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])
            
            if tool_calls:
                try:
                    decision = json.loads(tool_calls[0]["function"]["arguments"])
                    decision["response_to_user"] = content if content else ""
                    return decision
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
            
            return {
                "thought": content,
                "intent": "待分析",
                "tasks": [],
                "next_action": "continue",
                "is_complete": False,
                "response_to_user": content
            }
            
        except Exception as e:
            logger.error(f"[BrainAgent] Error analyzing intent: {e}")
            return {
                "thought": f"分析出错: {str(e)}",
                "intent": "error",
                "tasks": [],
                "next_action": "complete",
                "is_complete": True,
                "response_to_user": f"抱歉，分析过程中出现错误: {str(e)}"
            }

    async def decide_next_action(self, current_state: dict) -> dict:
        prompt = f"""基于当前任务状态，决定下一步行动。

原始请求: {current_state.get('original_request', '')}

已完成的步骤:
{json.dumps(current_state.get('completed_steps', []), ensure_ascii=False, indent=2)}

当前结果:
{json.dumps(current_state.get('current_results', {}), ensure_ascii=False, indent=2)}

请分析是否需要继续执行任务，或者任务已经完成可以生成总结。"""

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        context = current_state.get("context", {})
        
        try:
            result = await self.text_service.chat(
                messages=messages,
                model=context.get("model", "qwen-plus") if context else "qwen-plus",
                call_method="chat",
                api_key=context.get("api_key", "") if context else "",
                url=context.get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions") if context else "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                tools=self._get_tools_schema(),
                tool_choice={"type": "function", "function": {"name": "decide_action"}}
            )
            
            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])
            
            if tool_calls:
                try:
                    decision = json.loads(tool_calls[0]["function"]["arguments"])
                    decision["response_to_user"] = content if content else ""
                    return decision
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
            
            return {
                "thought": content,
                "next_action": "continue",
                "is_complete": False,
                "response_to_user": content
            }
            
        except Exception as e:
            logger.error(f"[BrainAgent] Error deciding next action: {e}")
            return {
                "thought": f"决策出错: {str(e)}",
                "next_action": "complete",
                "is_complete": True
            }

    async def generate_summary(self, task_history: list[dict], original_request: str, context: Optional[dict] = None) -> str:
        prompt = f"""请为以下任务执行过程生成总结。

原始请求: {original_request}

执行历史:
{json.dumps(task_history, ensure_ascii=False, indent=2)}

请生成一个清晰、简洁的总结，包括：
1. 完成了哪些任务
2. 得到了什么结果
3. 对用户的最终回复"""

        messages = [
            {"role": "system", "content": "你是一个任务总结助手，请生成清晰简洁的任务总结。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = await self.text_service.chat(
                messages=messages,
                model=context.get("model", "qwen-plus") if context else "qwen-plus",
                call_method="chat",
                api_key=context.get("api_key", "") if context else "",
                url=context.get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions") if context else "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            )
            
            return result.get("content", "任务已完成，但无法生成总结。")
            
        except Exception as e:
            logger.error(f"[BrainAgent] Error generating summary: {e}")
            return f"任务已完成。生成总结时出错: {str(e)}"

    async def dispatch_task(self, task: AgentTask, target_agent: str) -> AgentTask:
        logger.info(f"[BrainAgent] Dispatching task {task.task_id} to {target_agent}")
        task.status = "dispatched"
        task.metadata = task.metadata or {}
        task.metadata["dispatched_to"] = target_agent
        return task

    async def integrate_results(self, results: list[AgentTask]) -> dict:
        integrated = {
            "success": True,
            "outputs": [],
            "summary": ""
        }
        
        for result in results:
            if result.status == "completed":
                integrated["outputs"].append({
                    "task_id": result.task_id,
                    "output": result.result
                })
            else:
                integrated["success"] = False
        
        return integrated

    async def process(self, task: AgentTask) -> AgentTask:
        self.update_status(AgentStatus.THINKING)
        self.add_message("system", f"开始处理任务: {task.task_id}")
        
        try:
            context = task.metadata or {}
            intent_analysis = await self.analyze_intent(task.input_data, context)
            
            task.metadata = task.metadata or {}
            task.metadata["intent_analysis"] = intent_analysis
            
            self.update_status(AgentStatus.WORKING)
            self.add_message("assistant", f"意图分析完成: {intent_analysis.get('intent', '未知')}")
            
            task.status = "analyzed"
            task.result = intent_analysis
            
            self.update_status(AgentStatus.COMPLETED)
            
        except Exception as e:
            logger.error(f"[BrainAgent] Error processing task: {e}")
            task.status = "error"
            task.error = str(e)
            self.update_status(AgentStatus.ERROR)
            self.add_message("system", f"任务处理错误: {str(e)}")
        
        return task

    def get_capabilities(self) -> list[str]:
        return [
            "intent_analysis",
            "task_decomposition",
            "task_dispatch",
            "result_integration",
            "decision_making",
            "summary_generation"
        ]
