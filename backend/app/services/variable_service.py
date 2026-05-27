import json
import logging
import re
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models import RoomVariable
from app.cache import cache

logger = logging.getLogger(__name__)


class VariableService:
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    def __init__(self, db: Session):
        self.db = db

    def set_variable(self, room_id: str, name: str, value: Any, var_type: str = "string") -> bool:
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
                var_type = "json"
            elif not isinstance(value, str):
                value = str(value)
            
            existing = self.db.query(RoomVariable).filter(
                RoomVariable.room_id == room_id,
                RoomVariable.variable_name == name
            ).first()
            
            if existing:
                existing.variable_value = value
                existing.variable_type = var_type
            else:
                new_var = RoomVariable(
                    room_id=room_id,
                    variable_name=name,
                    variable_value=value,
                    variable_type=var_type
                )
                self.db.add(new_var)
            
            self.db.commit()
            
            cache_key = f"room_var:{room_id}:{name}"
            cache.set(cache_key, {"value": value, "type": var_type}, timeout=3600)
            
            # 如果批量缓存存在，直接更新而非删除重查
            bulk_cache_key = f"room_vars:{room_id}"
            cached_vars = cache.get(bulk_cache_key)
            if cached_vars is not None:
                cached_vars[name] = value
                cache.set(bulk_cache_key, cached_vars, timeout=3600)
            
            logger.info(f"[VariableService] Set variable: {name} for room: {room_id}")
            return True
        except Exception as e:
            logger.error(f"[VariableService] Error setting variable: {e}")
            self.db.rollback()
            return False

    def get_variable(self, room_id: str, name: str) -> Optional[Any]:
        try:
            cache_key = f"room_var:{room_id}:{name}"
            cached = cache.get(cache_key)
            if cached:
                value = cached["value"]
                if cached["type"] == "json":
                    return json.loads(value)
                return value
            
            var = self.db.query(RoomVariable).filter(
                RoomVariable.room_id == room_id,
                RoomVariable.variable_name == name
            ).first()
            
            if not var:
                return None
            
            cache.set(cache_key, {"value": var.variable_value, "type": var.variable_type}, timeout=3600)
            
            if var.variable_type == "json":
                return json.loads(var.variable_value)
            return var.variable_value
        except Exception as e:
            logger.error(f"[VariableService] Error getting variable: {e}")
            return None

    def get_all_variables(self, room_id: str) -> dict[str, Any]:
        try:
            cache_key = f"room_vars:{room_id}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            vars_query = self.db.query(RoomVariable).filter(
                RoomVariable.room_id == room_id
            ).all()
            
            result = {}
            for var in vars_query:
                if var.variable_type == "json":
                    result[var.variable_name] = json.loads(var.variable_value)
                else:
                    result[var.variable_name] = var.variable_value
            
            cache.set(cache_key, result, timeout=3600)
            return result
        except Exception as e:
            logger.error(f"[VariableService] Error getting all variables: {e}")
            return {}

    def resolve_variables(self, room_id: str, text: str) -> str:
        if not text or not isinstance(text, str):
            return text
        
        def replace_var(match):
            var_name = match.group(1)
            value = self.get_variable(room_id, var_name)
            if value is None:
                logger.warning(f"[VariableService] Variable not found: {var_name}")
                return match.group(0)
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            return str(value)
        
        return self.VARIABLE_PATTERN.sub(replace_var, text)

    def resolve_dict_variables(self, room_id: str, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.resolve_variables(room_id, value)
            elif isinstance(value, dict):
                result[key] = self.resolve_dict_variables(room_id, value)
            elif isinstance(value, list):
                result[key] = [
                    self.resolve_variables(room_id, item) if isinstance(item, str)
                    else self.resolve_dict_variables(room_id, item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def delete_variable(self, room_id: str, name: str) -> bool:
        try:
            self.db.query(RoomVariable).filter(
                RoomVariable.room_id == room_id,
                RoomVariable.variable_name == name
            ).delete()
            self.db.commit()
            
            cache.delete(f"room_var:{room_id}:{name}")
            cache.delete(f"room_vars:{room_id}")
            
            return True
        except Exception as e:
            logger.error(f"[VariableService] Error deleting variable: {e}")
            self.db.rollback()
            return False

    def clear_room_variables(self, room_id: str) -> bool:
        try:
            self.db.query(RoomVariable).filter(
                RoomVariable.room_id == room_id
            ).delete()
            self.db.commit()
            
            vars_query = self.db.query(RoomVariable.variable_name).filter(
                RoomVariable.room_id == room_id
            ).all()
            for (name,) in vars_query:
                cache.delete(f"room_var:{room_id}:{name}")
            cache.delete(f"room_vars:{room_id}")
            
            return True
        except Exception as e:
            logger.error(f"[VariableService] Error clearing room variables: {e}")
            self.db.rollback()
            return False
