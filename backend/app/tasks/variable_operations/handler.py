import logging
from typing import Optional
from app.services.variable_service import VariableService
from app.tasks.variable_operations.registry import (
    BaseVariableOperation,
    VariableOperationResult,
    variable_operation_registry
)

logger = logging.getLogger(__name__)


class SetVariableOperation(BaseVariableOperation):
    name = "set_variable"
    description = "设置变量的值，可以是字符串或 JSON 格式的数据"
    
    async def execute(self, **kwargs) -> VariableOperationResult:
        variable_service: Optional[VariableService] = kwargs.get("variable_service")
        room_id = kwargs.get("room_id", "")
        variable_name = kwargs.get("variable_name", "")
        variable_value = kwargs.get("variable_value")
        variable_type = kwargs.get("variable_type", "string")
        
        if not variable_name:
            return VariableOperationResult(
                success=False,
                output=None,
                error="缺少 variable_name 参数"
            )
        
        if variable_value is None:
            return VariableOperationResult(
                success=False,
                output=None,
                error="缺少 variable_value 参数"
            )
        
        if not variable_service:
            return VariableOperationResult(
                success=False,
                output=None,
                error="缺少 variable_service 参数"
            )
        
        try:
            success = variable_service.set_variable(room_id, variable_name, variable_value, variable_type)
            
            if not success:
                return VariableOperationResult(
                    success=False,
                    output=None,
                    error=f"无法设置变量: {variable_name}"
                )
            
            return VariableOperationResult(
                success=True,
                output={"variable_name": variable_name, "variable_type": variable_type}
            )
        except Exception as e:
            logger.error(f"[SetVariableOperation] Error: {e}")
            return VariableOperationResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "variable_name": {
                    "type": "string",
                    "description": "变量名称"
                },
                "variable_value": {
                    "type": "string",
                    "description": "变量值，可以是字符串或 JSON 格式"
                },
                "variable_type": {
                    "type": "string",
                    "enum": ["string", "json"],
                    "description": "变量类型，默认为 string"
                }
            },
            "required": ["variable_name", "variable_value"]
        }


class GetVariableOperation(BaseVariableOperation):
    name = "get_variable"
    description = "获取变量的值"
    
    async def execute(self, **kwargs) -> VariableOperationResult:
        variable_service: Optional[VariableService] = kwargs.get("variable_service")
        room_id = kwargs.get("room_id", "")
        variable_name = kwargs.get("variable_name", "")
        
        if not variable_name:
            return VariableOperationResult(
                success=False,
                output=None,
                error="缺少 variable_name 参数"
            )
        
        if not variable_service:
            return VariableOperationResult(
                success=False,
                output=None,
                error="缺少 variable_service 参数"
            )
        
        try:
            value = variable_service.get_variable(room_id, variable_name)
            
            if value is None:
                return VariableOperationResult(
                    success=False,
                    output=None,
                    error=f"变量不存在: {variable_name}"
                )
            
            return VariableOperationResult(
                success=True,
                output={"variable_name": variable_name, "value": value}
            )
        except Exception as e:
            logger.error(f"[GetVariableOperation] Error: {e}")
            return VariableOperationResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "variable_name": {
                    "type": "string",
                    "description": "要获取的变量名称"
                }
            },
            "required": ["variable_name"]
        }


variable_operation_registry.register(SetVariableOperation())
variable_operation_registry.register(GetVariableOperation())
