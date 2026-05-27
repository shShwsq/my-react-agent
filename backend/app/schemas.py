from datetime import datetime
from enum import Enum
from typing import Optional, Generic, TypeVar, Union

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class TaskErrorCode(str, Enum):
    """任务执行相关错误码"""
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TASK_TYPE_INVALID = "TASK_TYPE_INVALID"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    FILE_OP_NOT_FOUND = "FILE_OP_NOT_FOUND"
    FILE_OP_ERROR = "FILE_OP_ERROR"
    VAR_OP_NOT_FOUND = "VAR_OP_NOT_FOUND"
    VAR_OP_ERROR = "VAR_OP_ERROR"
    LLM_GEN_NOT_FOUND = "LLM_GEN_NOT_FOUND"
    LLM_GENERATION_ERROR = "LLM_GENERATION_ERROR"
    TASK_CONFIG_ERROR = "TASK_CONFIG_ERROR"

    @property
    def status(self) -> int:
        """所有任务错误都返回500服务器错误"""
        return 500

    @property
    def default_msg(self) -> str:
        messages = {
            "INTERNAL_ERROR": "服务器内部错误",
            "TASK_TYPE_INVALID": "不支持的任务类型",
            "TOOL_NOT_FOUND": "工具不存在",
            "TOOL_EXECUTION_ERROR": "工具执行失败",
            "FILE_OP_NOT_FOUND": "文件操作不存在",
            "FILE_OP_ERROR": "文件操作执行失败",
            "VAR_OP_NOT_FOUND": "变量操作不存在",
            "VAR_OP_ERROR": "变量操作执行失败",
            "LLM_GEN_NOT_FOUND": "LLM生成器不存在",
            "LLM_GENERATION_ERROR": "LLM生成失败",
            "TASK_CONFIG_ERROR": "任务配置错误",
        }
        return messages.get(self.value, "未知任务错误")

    @property
    def code(self) -> str:
        return self.value


class ErrorCode(str, Enum):
    AUTH_FAILED = "AUTH_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    USER_EXISTS = "USER_EXISTS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    API_ERROR = "API_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    @property
    def status(self) -> int:
        statuses = {
            "AUTH_FAILED": 401,
            "TOKEN_EXPIRED": 401,
            "TOKEN_INVALID": 401,
            "PERMISSION_DENIED": 403,
            "NOT_FOUND": 404,
            "USER_EXISTS": 400,
            "VALIDATION_ERROR": 422,
            "API_ERROR": 502,
            "INTERNAL_ERROR": 500,
        }
        return statuses.get(self.value, 500)

    @property
    def default_msg(self) -> str:
        messages = {
            "AUTH_FAILED": "用户名或密码错误",
            "TOKEN_EXPIRED": "登录已过期",
            "TOKEN_INVALID": "无效的登录凭证",
            "PERMISSION_DENIED": "没有权限",
            "NOT_FOUND": "资源不存在",
            "USER_EXISTS": "用户名已存在",
            "VALIDATION_ERROR": "参数验证失败",
            "API_ERROR": "外部API调用失败",
            "INTERNAL_ERROR": "服务器内部错误",
        }
        return messages.get(self.value, "未知错误")

    @property
    def code(self) -> str:
        return self.value


class ApiResponse(BaseModel, Generic[T]):
    e: str = ""
    d: Optional[T] = None
    m: str = ""


def success(data: T = None, message: str = "") -> ApiResponse[T]:
    return ApiResponse(e="", d=data, m=message)


class ApiException(HTTPException):
    def __init__(self, error_code: ErrorCode, message: Optional[str] = None):
        self.error_code = error_code
        self.message = message or error_code.default_msg
        super().__init__(
            status_code=error_code.status,
            detail=ApiResponse(e=error_code.code, d=None, m=self.message).model_dump()
        )


def fail(error_code: ErrorCode, message: Optional[str] = None) -> ApiException:
    return ApiException(error_code, message)


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class ProfileUpdate(BaseModel):
    username: str
    current_password: str
    new_password: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class MessageCreate(BaseModel):
    role: str
    content: str


class TextContent(BaseModel):
    type: str = "text"
    text: str


class ImageURL(BaseModel):
    url: str


class ImageContent(BaseModel):
    type: str = "image_url"
    image_url: ImageURL


MessageContent = Union[str, list[Union[TextContent, ImageContent, dict]]]


class MultimodalMessage(BaseModel):
    role: str
    content: MessageContent


class RoomCreate(BaseModel):
    id: str
    title: Optional[str] = None
    models: Optional[dict] = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    title: str
    models: Optional[dict]
    created_at: datetime
    messages: list["MessageResponse"] = []


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    messages: list[MessageCreate]
    model: str = "gpt-4o"
    provider: str = "aliyun"
    call_method: str = "chat"
    category: str = "text"
    sub_category: Optional[str] = None
    stream: bool = False
    config_id: Optional[int] = None
    base_url: str = ""


class ModelConfigCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    category: str
    sub_category: Optional[str] = None
    model_name: str
    provider: str = "aliyun"
    call_method: str = "chat"
    api_key: str = ""
    base_url: str = ""
    is_default: bool = False
    is_public: bool = False


class ModelConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    category: str
    sub_category: Optional[str] = None
    model_name: str
    provider: str
    call_method: str
    api_key: str
    base_url: str
    is_default: bool
    is_public: bool


class ASRRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    audio_data: str
    model: str = "paraformer-realtime-v2"
    provider: str = "aliyun"
    call_method: str = "dashscope"
    config_id: Optional[int] = None
    base_url: str = ""
    audio_format: str = "wav"
    stream: bool = False


class TTSRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str
    model: str = "cosyvoice-v1"
    provider: str = "aliyun"
    call_method: str = "websocket"
    config_id: Optional[int] = None
    base_url: str = ""
    voice: str = "longanyang"
    audio_format: str = "mp3"
    sample_rate: int = 22050
    stream: bool = False


class ImageGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt: str
    model: str = "wanx-v1"
    provider: str = "aliyun"
    call_method: str = "dashscope"
    config_id: Optional[int] = None
    base_url: str = ""
    size: str = "512*512"
    n: int = 1


class ImageUnderstandingRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    messages: list[MessageCreate]
    model: str = "qwen-vl-max"
    provider: str = "aliyun"
    call_method: str = "chat"
    config_id: Optional[int] = None
    base_url: str = ""
    stream: bool = False
    image_url: str = ""
