import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class VariableOperationResult:
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseVariableOperation(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, **kwargs) -> VariableOperationResult:
        pass
    
    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters()
        }
    
    @abstractmethod
    def get_parameters(self) -> dict:
        pass


class VariableOperationRegistry:
    def __init__(self):
        self._operations: dict[str, BaseVariableOperation] = {}
    
    def register(self, operation: BaseVariableOperation):
        self._operations[operation.name] = operation
        logger.info(f"[VariableOperationRegistry] Registered operation: {operation.name}")
    
    def get(self, name: str) -> Optional[BaseVariableOperation]:
        return self._operations.get(name)
    
    def list_operations(self) -> list[str]:
        return list(self._operations.keys())
    
    def get_all_schemas(self) -> list[dict]:
        return [op.get_schema() for op in self._operations.values()]


variable_operation_registry = VariableOperationRegistry()
