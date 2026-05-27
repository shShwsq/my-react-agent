from abc import ABC, abstractmethod
from typing import Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class AgentType(str, Enum):
    BRAIN = "brain"
    CHECK = "check"
    TASK = "task"


@dataclass
class AgentMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


@dataclass
class AgentTask:
    task_id: str
    task_type: str
    description: str
    input_data: Any
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Optional[dict] = None


@dataclass
class AgentState:
    agent_id: str
    agent_type: AgentType
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[AgentTask] = None
    message_history: list[AgentMessage] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type
        )

    def update_status(self, status: AgentStatus):
        self.state.status = status
        self.state.last_activity = datetime.utcnow()

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        message = AgentMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.state.message_history.append(message)
        self.state.last_activity = datetime.utcnow()

    def get_status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.state.status.value,
            "current_task": self.state.current_task.task_id if self.state.current_task else None,
            "message_count": len(self.state.message_history),
            "last_activity": self.state.last_activity.isoformat(),
        }

    @abstractmethod
    async def process(self, task: AgentTask) -> AgentTask:
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        pass
