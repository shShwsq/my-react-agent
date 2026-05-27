import json
import logging
from typing import Any, Optional
from app.agents.base import BaseAgent, AgentType, AgentTask, AgentStatus
from app.services.text_service import TextService
from app.database import SessionLocal
from app.models import Message

logger = logging.getLogger(__name__)


class CheckAgent(BaseAgent):
    def __init__(self, agent_id: str = "check-001"):
        super().__init__(agent_id, AgentType.CHECK)
        self.text_service = TextService()
        self.check_rules: dict[str, list[dict]] = {}

    def add_check_rule(self, rule_type: str, rule: dict):
        if rule_type not in self.check_rules:
            self.check_rules[rule_type] = []
        self.check_rules[rule_type].append(rule)

    def _get_tools_schema(self) -> list[dict]:
        return [{
            "type": "function",
            "function": {
                "name": "check_task_completion",
                "description": "检查任务是否已完成",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_complete": {
                            "type": "boolean",
                            "description": "任务是否已完成"
                        },
                        "completion_score": {
                            "type": "number",
                            "description": "完成度评分 0.0-1.0"
                        },
                        "reason": {
                            "type": "string",
                            "description": "判断理由"
                        },
                        "summary": {
                            "type": "string",
                            "description": "任务完成总结（is_complete为true时必填）"
                        },
                        "response_to_user": {
                            "type": "string",
                            "description": "给用户的回复（is_complete为true时必填）"
                        },
                        "missing_aspects": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "未完成的方面"
                        },
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "改进建议"
                        }
                    },
                    "required": ["is_complete", "completion_score", "reason"]
                }
            }
        }]

    async def validate_result(self, result: Any, criteria: dict) -> dict:
        validation = {
            "is_valid": True,
            "score": 1.0,
            "issues": [],
            "suggestions": []
        }
        
        if criteria.get("min_length"):
            if len(str(result)) < criteria["min_length"]:
                validation["is_valid"] = False
                validation["issues"].append(f"结果长度不足，最少需要 {criteria['min_length']} 字符")
        
        if criteria.get("required_fields"):
            if isinstance(result, dict):
                for field in criteria["required_fields"]:
                    if field not in result:
                        validation["is_valid"] = False
                        validation["issues"].append(f"缺少必要字段: {field}")
        
        return validation

    async def quality_check(self, content: str) -> dict:
        quality = {
            "readability": 0.8,
            "completeness": 0.9,
            "accuracy": 0.85,
            "overall_score": 0.85,
            "feedback": []
        }
        
        if len(content) < 10:
            quality["completeness"] = 0.3
            quality["feedback"].append("回复内容过短")
        
        if "错误" in content or "失败" in content:
            quality["accuracy"] = 0.5
            quality["feedback"].append("回复可能包含错误信息")
        
        quality["overall_score"] = (
            quality["readability"] * 0.3 +
            quality["completeness"] * 0.4 +
            quality["accuracy"] * 0.3
        )
        
        return quality

    async def check_task_completion_stream(
        self, 
        original_request: str,
        current_result: Any,
        task_history: list[dict],
        context: Optional[dict] = None
    ):
        """流式检查任务完成度，使用Function Calling获取结构化结果"""
        
        # 从对话历史中提取所有用户消息，让 check agent 考虑全部用户请求
        user_requests = [original_request]
        if context and context.get("conversation_history"):
            for msg in context["conversation_history"]:
                if msg.get("role") == "user":
                    user_requests.append(msg["content"])
        
        user_requests_str = "\n".join(f"- {r}" for r in user_requests)
        
        prompt = f"""请检查任务是否已完成。

用户请求（请综合考虑所有请求）:
{user_requests_str}

当前执行结果:
{json.dumps(current_result, ensure_ascii=False, indent=2) if isinstance(current_result, (dict, list)) else str(current_result)}

执行历史:
{json.dumps(task_history, ensure_ascii=False, indent=2)}

请判断：
1. 用户的所有请求是否均已满足？
2. 结果是否满足用户的全部需求？
3. 是否需要继续执行更多步骤来满足剩余的用户请求？"""

        system_content = "你是一个任务完成度检查助手，负责判断任务是否已经完成。"
        
        # 历史对话：标准role直接追加，智能体role拼入system prompt
        agent_context_parts = []
        messages = [
            {"role": "system", "content": system_content}
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
        
        messages.append({"role": "user", "content": prompt})
        
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
                tool_choice={"type": "function", "function": {"name": "check_task_completion"}}
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
            
            if tool_calls_data:
                combined_args = ""
                for tc in tool_calls_data:
                    if "function" in tc and "arguments" in tc["function"] and tc["function"]["arguments"] is not None:
                        combined_args += tc["function"]["arguments"]
                
                try:
                    result = json.loads(combined_args)
                    for field in ["missing_aspects", "suggestions"]:
                        if isinstance(result.get(field), str):
                            try:
                                result[field] = json.loads(result[field])
                            except json.JSONDecodeError:
                                result[field] = []
                except json.JSONDecodeError:
                    result = {
                        "is_complete": False,
                        "completion_score": 0.5,
                        "reason": combined_args,
                        "summary": "",
                        "response_to_user": "",
                        "missing_aspects": [],
                        "suggestions": []
                    }
            else:
                result = {
                    "is_complete": False,
                    "completion_score": 0.5,
                    "reason": full_content,
                    "summary": "",
                    "response_to_user": full_content,
                    "missing_aspects": [],
                    "suggestions": []
                }
            
            if not result.get("response_to_user"):
                result["response_to_user"] = full_content if full_content else ""
            
            yield ("result", result)
            
            # 保存结果到数据库
            room_id = context.get("room_id", "") if context else ""
            if room_id:
                try:
                    db = SessionLocal()
                    msg = Message(room_id=room_id, role="check", content=json.dumps(result, ensure_ascii=False))
                    db.add(msg)
                    db.commit()
                    db.close()
                except Exception as e:
                    logger.error(f"[CheckAgent] Failed to save result: {e}")
            
        except Exception as e:
            logger.error(f"[CheckAgent] Error in stream check: {e}")
            yield ("error", {"error": str(e)})

    async def check_task_completion(
        self, 
        original_request: str,
        current_result: Any,
        task_history: list[dict],
        context: Optional[dict] = None
    ) -> dict:
        prompt = f"""请检查任务是否已完成。

原始请求: {original_request}

当前执行结果:
{json.dumps(current_result, ensure_ascii=False, indent=2) if isinstance(current_result, (dict, list)) else str(current_result)}

执行历史:
{json.dumps(task_history, ensure_ascii=False, indent=2)}

请判断：
1. 任务是否已经完成？
2. 结果是否满足用户的原始需求？
3. 是否需要继续执行更多步骤？"""

        messages = [
            {"role": "system", "content": "你是一个任务完成度检查助手，负责判断任务是否已经完成。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = await self.text_service.chat(
                messages=messages,
                model=context.get("model", "qwen-plus") if context else "qwen-plus",
                call_method=context.get("call_method", "chat") if context else "chat",
                api_key=context.get("api_key", "") if context else "",
                url=context.get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions") if context else "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                tools=self._get_tools_schema(),
                tool_choice={"type": "function", "function": {"name": "check_task_completion"}}
            )
            
            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])
            
            if tool_calls:
                try:
                    check_result = json.loads(tool_calls[0]["function"]["arguments"])
                    return check_result
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
            
            return {
                "is_complete": False,
                "completion_score": 0.5,
                "reason": content,
                "summary": "",
                "response_to_user": "",
                "missing_aspects": [],
                "suggestions": []
            }
            
        except Exception as e:
            logger.error(f"[CheckAgent] Error checking task completion: {e}")
            return {
                "is_complete": False,
                "completion_score": 0.0,
                "reason": f"检查出错: {str(e)}",
                "summary": "",
                "response_to_user": "",
                "missing_aspects": [],
                "suggestions": []
            }

    async def suggest_improvements(self, result: Any, issues: list[str]) -> list[dict]:
        suggestions = []
        
        for issue in issues:
            suggestion = {
                "issue": issue,
                "suggestion": f"建议修复: {issue}",
                "priority": "medium"
            }
            suggestions.append(suggestion)
        
        return suggestions

    async def process(self, task: AgentTask) -> AgentTask:
        self.update_status(AgentStatus.THINKING)
        self.add_message("system", f"开始检查任务: {task.task_id}")
        
        try:
            criteria = task.metadata.get("check_criteria", {}) if task.metadata else {}
            
            validation = await self.validate_result(task.input_data, criteria)
            
            quality = await self.quality_check(str(task.input_data))
            
            if not validation["is_valid"]:
                suggestions = await self.suggest_improvements(
                    task.input_data, 
                    validation["issues"]
                )
            else:
                suggestions = []
            
            task.result = {
                "validation": validation,
                "quality": quality,
                "suggestions": suggestions
            }
            
            task.status = "completed"
            self.update_status(AgentStatus.COMPLETED)
            self.add_message("assistant", f"检查完成，质量评分: {quality['overall_score']:.2f}")
            
        except Exception as e:
            logger.error(f"[CheckAgent] Error processing task: {e}")
            task.status = "error"
            task.error = str(e)
            self.update_status(AgentStatus.ERROR)
            self.add_message("system", f"检查任务错误: {str(e)}")
        
        return task

    def get_capabilities(self) -> list[str]:
        return [
            "result_validation",
            "quality_check",
            "error_detection",
            "improvement_suggestion",
            "compliance_check",
            "task_completion_check"
        ]
