import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncGenerator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LLMGenerateResult:
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseLLMGenerate(ABC):
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


class LLMGenerateRegistry:
    def __init__(self):
        self._generators: dict[str, BaseLLMGenerate] = {}
    
    def register(self, generator: BaseLLMGenerate):
        self._generators[generator.name] = generator
        logger.info(f"[LLMGenerateRegistry] Registered generator: {generator.name}")
    
    def get(self, name: str) -> Optional[BaseLLMGenerate]:
        return self._generators.get(name)
    
    def list_generators(self) -> list[str]:
        return list(self._generators.keys())
    
    def get_all_schemas(self) -> list[dict]:
        return [gen.get_schema() for gen in self._generators.values()]


llm_generate_registry = LLMGenerateRegistry()
