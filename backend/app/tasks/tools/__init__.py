import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
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


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
        logger.info(f"[ToolRegistry] Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
    
    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> list[dict]:
        return [tool.get_schema() for tool in self._tools.values()]


tool_registry = ToolRegistry()

import app.tasks.tools.tq_tools
