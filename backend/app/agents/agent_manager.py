import asyncio
import logging
import uuid
from typing import Any, Optional
from datetime import datetime

from app.agents.base import BaseAgent, AgentType, AgentTask, AgentStatus
from app.agents.brain_agent import BrainAgent
from app.agents.check_agent import CheckAgent
from app.agents.task_agent import TaskAgent

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self):
        self.brain_agent = BrainAgent()
        self.check_agent = CheckAgent()
        self.task_agent = TaskAgent()
        
        self.agents: dict[str, BaseAgent] = {
            "brain": self.brain_agent,
            "check": self.check_agent,
            "task": self.task_agent,
        }
        
        self.active_tasks: dict[str, AgentTask] = {}
        self.task_history: list[AgentTask] = []
        
        self._setup_agent_connections()

    def _setup_agent_connections(self):
        self.brain_agent.register_sub_agent("task", self.task_agent.agent_id)
        self.brain_agent.register_sub_agent("check", self.check_agent.agent_id)

    def get_all_agents_status(self) -> dict:
        return {
            "agents": [agent.get_status() for agent in self.agents.values()],
            "active_tasks": len(self.active_tasks),
            "total_completed": len(self.task_history),
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_agent_status(self, agent_type: str) -> Optional[dict]:
        agent = self.agents.get(agent_type)
        return agent.get_status() if agent else None

    def create_task(
        self, 
        task_type: str, 
        description: str, 
        input_data: Any,
        metadata: Optional[dict] = None
    ) -> AgentTask:
        task_id = str(uuid.uuid4())[:8]
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            description=description,
            input_data=input_data,
            metadata=metadata
        )
        self.active_tasks[task_id] = task
        return task

    async def process_with_brain(self, user_input: str, context: Optional[dict] = None) -> dict:
        task = self.create_task(
            task_type="intent_analysis",
            description="分析用户意图",
            input_data=user_input,
            metadata=context
        )
        
        result_task = await self.brain_agent.process(task)
        
        self._archive_task(task)
        
        return {
            "task_id": task.task_id,
            "status": result_task.status,
            "result": result_task.result,
            "error": result_task.error
        }

    async def process_with_task_agent(
        self, 
        task_type: str, 
        input_data: Any,
        context: Optional[dict] = None
    ) -> dict:
        task = self.create_task(
            task_type=task_type,
            description=f"执行{task_type}任务",
            input_data=input_data,
            metadata=context
        )
        
        result_task = await self.task_agent.process(task)
        
        self._archive_task(task)
        
        return {
            "task_id": task.task_id,
            "status": result_task.status,
            "result": result_task.result,
            "error": result_task.error
        }

    async def check_result(self, result: Any, criteria: Optional[dict] = None) -> dict:
        task = self.create_task(
            task_type="validation",
            description="验证结果质量",
            input_data=result,
            metadata={"check_criteria": criteria or {}}
        )
        
        result_task = await self.check_agent.process(task)
        
        self._archive_task(task)
        
        return {
            "task_id": task.task_id,
            "status": result_task.status,
            "result": result_task.result,
            "error": result_task.error
        }

    async def full_pipeline(self, user_input: str, context: Optional[dict] = None) -> dict:
        pipeline_result = {
            "pipeline_id": str(uuid.uuid4())[:8],
            "stages": [],
            "final_result": None,
            "status": "processing"
        }
        
        try:
            brain_result = await self.process_with_brain(user_input, context)
            pipeline_result["stages"].append({
                "stage": "brain",
                "result": brain_result
            })
            
            if brain_result["status"] == "completed":
                intent = brain_result["result"]
                task_type = intent.get("task_type", "text_generation")
                
                task_result = await self.process_with_task_agent(
                    task_type, 
                    user_input, 
                    context
                )
                pipeline_result["stages"].append({
                    "stage": "task",
                    "result": task_result
                })
                
                if task_result["status"] == "completed":
                    check_result = await self.check_result(
                        task_result["result"],
                        {"min_length": 10}
                    )
                    pipeline_result["stages"].append({
                        "stage": "check",
                        "result": check_result
                    })
                    
                    if check_result["result"]["validation"]["is_valid"]:
                        pipeline_result["final_result"] = task_result["result"]
                        pipeline_result["status"] = "completed"
                    else:
                        pipeline_result["status"] = "needs_revision"
                        pipeline_result["issues"] = check_result["result"]["validation"]["issues"]
                else:
                    pipeline_result["status"] = "task_failed"
            else:
                pipeline_result["status"] = "brain_failed"
                
        except Exception as e:
            logger.error(f"[AgentManager] Pipeline error: {e}")
            pipeline_result["status"] = "error"
            pipeline_result["error"] = str(e)
        
        return pipeline_result

    def _archive_task(self, task: AgentTask):
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        task.completed_at = datetime.utcnow()
        self.task_history.append(task)
        
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-50:]

    def reset_all_agents(self):
        for agent in self.agents.values():
            agent.update_status(AgentStatus.IDLE)
            agent.state.current_task = None
        
        self.active_tasks.clear()
        logger.info("[AgentManager] All agents reset to idle state")
