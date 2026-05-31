from typing import Optional



MODEL_CATEGORIES = {
    "text": {
        "label": "文本模型",
        "sub_categories": None,
    },
    "voice": {
        "label": "语音模型",
        "sub_categories": {
            "asr": "语音识别",
            "tts": "语音合成",
        },
    },
    "vision": {
        "label": "视觉模型",
        "sub_categories": {
            "image_understanding": "图片理解",
            "image_generation": "图片生成",
        },
    },
}

PROVIDER_CALL_METHODS = {
    "text": {
        "aliyun": [
            {"value": "chat", "label": "OpenAI兼容-Chat"},
            {"value": "responses", "label": "OpenAI兼容-Responses"},
            {"value": "messages", "label": "Anthropic兼容-Messages"},
            {"value": "dashscope", "label": "Dashscope"},
        ],
    },
    "voice_asr": {
        "aliyun": [
            {"value": "openai", "label": "OpenAI兼容"},
            {"value": "dashscope", "label": "Dashscope"},
        ],
    },
    "voice_tts": {
        "aliyun": [
            {"value": "websocket", "label": "WebSocket"},
        ],
    },
    "vision_image_understanding": {
        "aliyun": [
            {"value": "chat", "label": "OpenAI兼容-Chat"},
            {"value": "messages", "label": "Anthropic兼容-Messages"},
            {"value": "dashscope", "label": "Dashscope"},
        ],
    },
    "vision_image_generation": {
        "aliyun": [
            {"value": "dashscope", "label": "Dashscope"},
        ],
    },
}

PROVIDER_URLS = {
    "text": {
        "aliyun": {
            "chat": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "responses": "https://dashscope.aliyuncs.com/compatible-mode/v1/responses",
            "messages": "https://dashscope.aliyuncs.com/apps/anthropic/v1/messages",
            "dashscope": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        },
    },
    "voice_asr": {
        "aliyun": {
            "openai": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "dashscope": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        },
    },
    "voice_tts": {
        "aliyun": {
            "websocket": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
        },
    },
    "vision_image_understanding": {
        "aliyun": {
            "chat": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "messages": "https://dashscope.aliyuncs.com/apps/anthropic/v1/messages",
            "dashscope": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        },
    },
    "vision_image_generation": {
        "aliyun": {
            "dashscope": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        },
    },
}

MODEL_NAMES = {
    "text": {
        "aliyun": {
            "chat": [
                "qwen3.6-plus",
                "qwen3.6-flash",
                "qwen3.6-plus-2026-04-02",
                "qwen3.5-plus-2026-02-15",
                "qwen3.5-plus-2026-04-20",
                "qwen3.5-flash-2026-02-15",
                "qwen3.5-27b",
                "qwen3.5-35b-a3b",
                "glm-4.5",
                "qwen-plus-2025-07-14",
                "qwen-plus-2025-04-28",
                "qwen3-30b-a3b",
                "qwen-plus-2025-01-25",
                "qwen-flash-2025-07-28",
                "qwen3.6-35b-a3b",
            ],
            "responses": [
                "qwen3-max",
                "qwen3-max-2026-01-23",
                "qwen3.6-plus",
                "qwen3.6-plus-2026-04-02",
                "qwen3.5-plus",
                "qwen3.5-plus-2026-04-20",
                "qwen3.5-plus-2026-02-15",
                "qwen3.6-flash",
                "qwen3.6-flash-2026-04-16",
                "qwen3.5-flash",
                "qwen3.5-flash-2026-02-23",
                "qwen3.6-35b-a3b",
                "qwen3.5-397b-a17b",
                "qwen3.5-122b-a10b",
                "qwen3.5-35b-a3b",
                "qwen3.5-27b",
                "qwen-plus",
                "qwen-flash",
            ],
            "messages": [
                "qwen3.6-max-preview",
                "qwen3-max",
                "qwen3-max-2026-01-23",
                "qwen3-max-preview",
                "qwen3.6-plus",
                "qwen3.6-plus-2026-04-02",
                "qwen3.5-plus",
                "qwen3.5-plus-2026-04-20",
                "qwen3.5-plus-2026-02-15",
                "qwen-plus",
                "qwen-plus-latest",
                "qwen-plus-2025-09-11",
                "qwen3.6-flash",
                "qwen3.6-flash-2026-04-16",
                "qwen3.5-flash",
                "qwen3.5-flash-2026-02-23",
                "qwen-flash",
                "qwen-flash-2025-07-28",
                "qwen3.6-27b",
                "qwen3.5-397b-a17b",
                "qwen3.5-122b-a10b",
                "qwen3.5-27b",
                "qwen3.5-35b-a3b",
            ],
            "dashscope": [
                "qwen3.6-plus",
                "qwen3.6-flash",
                "qwen3.6-plus-2026-04-02",
                "qwen3.5-plus-2026-02-15",
                "qwen3.5-flash-2026-02-15",
                "qwen3.5-27b",
                "qwen3.5-35b-a3b",
                "qwen3.6-35b-a3b",
            ],
        },
    },
    "voice_asr": {
        "aliyun": {
            "openai": [
                "qwen3-asr-flash",
                "qwen3-asr-flash-2026-02-10",
                "qwen3-asr-flash-2025-09-08",
            ],
            "dashscope": [
                "qwen3-asr-flash",
                "qwen3-asr-flash-2026-02-10",
            ],
        },
    },
    "voice_tts": {
        "aliyun": {
            "websocket": [
                "cosyvoice-v2",
                "cosyvoice-v3-flash",
                "cosyvoice-v3-plus",
                "cosyvoice-v3.5-flash",
                "cosyvoice-v3.5-plus",
            ],
        },
    },
    "vision_image_understanding": {
        "aliyun": {
            "chat": [
                "qwen3.5-omni-plus",
                "qwen-vl-max",
                "qwen-vl-plus",
                "qwen2.5-vl-72b-instruct",
                "qwen2.5-vl-32b-instruct",
                "qwen2.5-vl-7b-instruct",
                "qwen2.5-vl-3b-instruct",
                "qwen3-vl-max",
                "qwen3-vl-plus",
                "qwen3-vl-flash-2025-10-15",
                "qwen3-vl-plus-2025-12-19",
            ],
            "messages": [
                "qwen3-vl-plus",
                "qwen3-vl-flash",
                "qwen-vl-max",
                "qwen-vl-plus",
                "qwen3.6-plus",
                "qwen3.6-plus-2026-04-02",
                "qwen3.5-plus",
                "qwen3.5-plus-2026-04-20",
                "qwen3.5-plus-2026-02-15",
                "qwen-plus",
                "qwen-plus-latest",
                "qwen-plus-2025-09-11",
                "qwen3.6-flash",
                "qwen3.6-flash-2026-04-16",
                "qwen3.5-flash",
                "qwen3.5-flash-2026-02-23",
                "qwen-flash",
                "qwen-flash-2025-07-28",
            ],
            "dashscope": [
                "qwen-vl-max",
                "qwen-vl-plus",
                "qwen2.5-vl-72b-instruct",
                "qwen2.5-vl-32b-instruct",
                "qwen2.5-vl-7b-instruct",
                "qwen2.5-vl-3b-instruct",
                "qwen3-vl-max",
                "qwen3-vl-plus",
                                "qwen3.6-plus",
                "qwen3.6-plus-2026-04-02",
                "qwen3.5-plus",
                "qwen3.5-plus-2026-04-20",
                "qwen3.5-plus-2026-02-15",
                "qwen-plus",
                "qwen-plus-latest",
                "qwen-plus-2025-09-11",
                "qwen3.6-flash",
                "qwen3.6-flash-2026-04-16",
                "qwen3.5-flash",
                "qwen3.5-flash-2026-02-23",
                "qwen-flash",
                "qwen-flash-2025-07-28",
            ],
        },
    },
    "vision_image_generation": {
        "aliyun": {
            "dashscope": [
                "qwen-image-2.0",
                "qwen-image-2.0-pro",
                "qwen-image-2.0-2026-03-03",
                "qwen-image-max-2025-12-30",
            ],
        },
    },
}


def get_model_categories() -> dict:
    return MODEL_CATEGORIES


def get_provider_call_methods(category: str, sub_category: Optional[str], provider: str) -> list[dict]:
    if sub_category:
        key = f"{category}_{sub_category}"
    else:
        key = category
    
    category_config = PROVIDER_CALL_METHODS.get(key, {})
    return category_config.get(provider, [])


def get_model_names(provider: str, call_method: str, category: str, sub_category: Optional[str] = None) -> list[str]:
    if sub_category:
        key = f"{category}_{sub_category}"
    else:
        key = category
    
    category_config = MODEL_NAMES.get(key, {})
    provider_config = category_config.get(provider, {})
    return provider_config.get(call_method, [])


def get_default_url(provider: str, call_method: str, category: str, sub_category: Optional[str] = None) -> str:
    if sub_category:
        key = f"{category}_{sub_category}"
    else:
        key = category
    
    category_config = PROVIDER_URLS.get(key, {})
    provider_config = category_config.get(provider, {})
    return provider_config.get(call_method, "")


def build_request_url(user_url: str, call_method: str) -> str:
    if not user_url:
        return user_url
    
    stripped = user_url.rstrip("/")
    
    if stripped.endswith("/v1"):
        if call_method == "responses":
            return stripped + "/responses"
        if call_method == "messages":
            return stripped + "/messages"
        return stripped + "/chat/completions"
    
    if stripped.endswith("/v1/chat/completions"):
        return stripped
    if stripped.endswith("/v1/responses"):
        return stripped
    if stripped.endswith("/v1/messages"):
        return stripped
    
    return user_url
