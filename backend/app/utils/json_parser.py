import json
import logging
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)

try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False
    logger.warning("[RobustJSONParser] json_repair not installed, using fallback parser")


class RobustJSONParser:
    """
    容错性强的 JSON 解析器，专门处理 LLM 输出的 JSON 字符串。
    
    优先使用 json_repair 库，失败后回退到自定义解析器。
    """
    
    @staticmethod
    def parse(text: str) -> Optional[Union[dict, list]]:
        """
        尝试多种方法解析 JSON 字符串。
        
        Args:
            text: 可能包含 JSON 的字符串
            
        Returns:
            解析后的 dict 或 list，失败返回 None
        """
        if not text or not isinstance(text, str):
            logger.debug(f"[RobustJSONParser] Invalid input: type={type(text)}")
            return None
        
        text = text.strip()
        
        try:
            result = json.loads(text)
            logger.debug(f"[RobustJSONParser] Successfully parsed with json.loads")
            return result
        except Exception as e:
            logger.debug(f"[RobustJSONParser] json.loads failed: {e}")
        
        if HAS_JSON_REPAIR:
            try:
                fixed = repair_json(text)
                result = json.loads(fixed)
                logger.debug(f"[RobustJSONParser] Successfully parsed with json_repair")
                return result
            except Exception as e:
                logger.debug(f"[RobustJSONParser] json_repair failed: {e}")
        
        logger.warning(f"[RobustJSONParser] All parsers failed for text (length={len(text)})")
        return None
    
    @staticmethod
    def parse_tasks(tasks_str: Any) -> list:
        """
        专门解析 tasks 字段，处理字符串形式的 tasks。
        
        Args:
            tasks_str: 可能是 list 或 str 类型的 tasks
            
        Returns:
            解析后的 tasks 列表
        """
        if isinstance(tasks_str, list):
            return tasks_str
        
        if not isinstance(tasks_str, str):
            logger.warning(f"[RobustJSONParser] tasks is not string or list")
            return []
        
        result = RobustJSONParser.parse(tasks_str)
        
        if isinstance(result, list):
            return result
        
        if isinstance(result, dict):
            logger.warning(f"[RobustJSONParser] tasks parsed as dict, wrapping in list")
            return [result]
        
        logger.warning(f"[RobustJSONParser] Failed to parse tasks string")
        return []


def parse_llm_json(text: str) -> Optional[Union[dict, list]]:
    """
    便捷函数：解析 LLM 输出的 JSON。
    
    Args:
        text: LLM 输出的文本
        
    Returns:
        解析后的对象
    """
    return RobustJSONParser.parse(text)


def parse_llm_tasks(tasks_str: Any) -> list:
    """
    便捷函数：解析 LLM 输出的 tasks 字段。
    
    Args:
        tasks_str: tasks 字段的值（可能是字符串或列表）
        
    Returns:
        tasks 列表
    """
    return RobustJSONParser.parse_tasks(tasks_str)
