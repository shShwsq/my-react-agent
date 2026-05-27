import json
import logging
from typing import Optional, AsyncGenerator
from app.services.text_service import TextService
from app.services.variable_service import VariableService
from app.tasks.llm_generate.registry import (
    BaseLLMGenerate,
    llm_generate_registry
)
from app.schemas import ApiResponse

logger = logging.getLogger(__name__)


def gen_success(data: dict) -> str:
    """构建LLM生成成功的响应"""
    return ApiResponse(e="", m="", d=data).model_dump_json()


def gen_error(error_code: str, message: str) -> str:
    """构建LLM生成失败的响应"""
    return ApiResponse(e=error_code, m=message, d=None).model_dump_json()


class ContentGenerator(BaseLLMGenerate):
    name = "content_generator"
    description = "调用大语言模型生成内容，并将结果存储到变量中。适用于需要生成大量文本内容的场景。"
    
    def __init__(self, text_service: Optional[TextService] = None):
        self.text_service = text_service or TextService()
    
    async def execute(self, **kwargs):
        prompt = kwargs.get("prompt", "")
        output_variable = kwargs.get("output_variable", "")
        
        api_key = kwargs.get("api_key", "")
        api_url = kwargs.get("api_url", "")
        model = kwargs.get("model", "qwen-plus")
        call_method = kwargs.get("call_method", "chat")
        
        variable_service: Optional[VariableService] = kwargs.get("variable_service")
        room_id = kwargs.get("room_id", "")
        
        if not prompt:
            yield gen_error("LLM_GENERATION_ERROR", "缺少 prompt 参数")
            return
        
        if not output_variable:
            yield gen_error("LLM_GENERATION_ERROR", "缺少 output_variable 参数")
            return
        
        if not variable_service:
            yield gen_error("LLM_GENERATION_ERROR", "缺少 variable_service 参数")
            return
        
        if not api_key:
            yield gen_error("LLM_GENERATION_ERROR", "缺少 API Key 配置")
            return
        
        full_content = ""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            async for chunk in self.text_service.stream_chat(
                messages=messages,
                model=model,
                api_key=api_key,
                url=api_url,
                call_method=call_method
            ):
                if chunk.startswith("data: "):
                    data_str = chunk[6:].strip()
                    if data_str and data_str != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            if "content" in data:
                                content_piece = data["content"]
                                full_content += content_piece
                                yield gen_success({"type": "content", "content": content_piece})
                        except json.JSONDecodeError:
                            pass
            
            if not full_content:
                yield gen_error("LLM_GENERATION_ERROR", "LLM 未生成任何内容")
                return
            
            success = variable_service.set_variable(room_id, output_variable, full_content)
            
            if not success:
                yield gen_error("LLM_GENERATION_ERROR", f"无法存储变量: {output_variable}")
                return
            
            logger.info(f"[ContentGenerator] Generated content stored in variable: {output_variable}, length: {len(full_content)}")
            
            yield gen_success({
                "type": "complete",
                "variable_name": output_variable,
                "content_length": len(full_content),
                "variable_value": full_content
            })
            
        except Exception as e:
            logger.error(f"[ContentGenerator] Error: {e}")
            yield gen_error("LLM_GENERATION_ERROR", str(e))
    
    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "生成内容的提示词，描述需要生成的内容"
                },
                "output_variable": {
                    "type": "string",
                    "description": "存储生成内容的变量名，后续可通过 {{变量名}} 引用"
                }
            },
            "required": ["prompt", "output_variable"]
        }


llm_generate_registry.register(ContentGenerator())
