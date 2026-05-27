import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, text, models, voice, vision, rooms, agents, brain_agent, check_agent, task_agent, agent_loop, files, user_preferences

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(text.router)
app.include_router(models.router)
app.include_router(voice.router)
app.include_router(vision.router)
app.include_router(rooms.router)
app.include_router(agents.router)
app.include_router(brain_agent.router)
app.include_router(check_agent.router)
app.include_router(task_agent.router)
app.include_router(agent_loop.router)
app.include_router(files.router)
app.include_router(user_preferences.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/deploy-config")
def deploy_config():
    """返回部署配置，供前端获取外部访问地址等信息"""
    return {
        "frontend_external_url": os.environ.get("FRONTEND_EXTERNAL_URL", ""),
        "locust_proxy_path": os.environ.get("LOCUST_PROXY_PATH", "/locust/"),
    }
