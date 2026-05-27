import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncGenerator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ImageOperationResult:
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseImageOperation(ABC):
    name: str
    description: str
    
    @abstractmethod
    def execute(self, **kwargs) -> AsyncGenerator[str, None]:
        ...
    
    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters()
        }
    
    @abstractmethod
    def get_parameters(self) -> dict:
        pass


class ImageOperationRegistry:
    def __init__(self):
        self._operations: dict[str, BaseImageOperation] = {}
    
    def register(self, operation: BaseImageOperation):
        self._operations[operation.name] = operation
        logger.info(f"[ImageOperationRegistry] Registered operation: {operation.name}")
    
    def get(self, name: str) -> Optional[BaseImageOperation]:
        return self._operations.get(name)
    
    def list_operations(self) -> list[str]:
        return list(self._operations.keys())
    
    def get_all_schemas(self) -> list[dict]:
        return [op.get_schema() for op in self._operations.values()]


image_operation_registry = ImageOperationRegistry()
