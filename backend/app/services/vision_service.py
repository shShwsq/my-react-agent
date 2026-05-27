import base64
import json
import logging
from typing import AsyncGenerator

import httpx

from .text_service import TextService

logger = logging.getLogger(__name__)


class VisionService:
    def __init__(self):
        self.text_service = TextService()

    async def image_generation(
        self,
        prompt: str,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        size: str = "512*512",
        n: int = 1,
        **kwargs,
    ) -> dict:
        if not api_key:
            raise ValueError("API Key 未配置，请在模型配置中设置 API Key")

        logger.info(f"[VisionService] image_generation kwargs: {kwargs}")

        if call_method == "dashscope":
            return await self._dashscope_image_generation(prompt, model, api_key, url, size, n, **kwargs)
        else:
            return await self._dashscope_image_generation(prompt, model, api_key, url, size, n, **kwargs)


    async def _dashscope_image_generation(
        self,
        prompt: str,
        model: str,
        api_key: str,
        url: str,
        size: str,
        n: int,
        **kwargs,
    ) -> dict:
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ],
            },
            "parameters": {
                "size": size,
                "n": n,
            },
        }
        
        optional_params = ["negative_prompt", "prompt_extend", "watermark", "seed"]
        for param in optional_params:
            if param in kwargs and kwargs[param] is not None:
                payload["parameters"][param] = kwargs[param]
        
        logger.info(f"[VisionService] DashScope Image Generation Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self._get_headers(api_key, "dashscope"), json=payload)
                if response.status_code == 401:
                    raise ValueError("API Key 无效或已过期")
                if response.status_code == 404:
                    raise ValueError(f"API 端点不存在，请检查 URL: {url}")
                
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"[VisionService] DashScope Image Generation Error - Status: {response.status_code}, Response: {error_detail}")
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            raise ValueError(f"API 错误: {error_json['message']}")
                        elif "error" in error_json:
                            raise ValueError(f"API 错误: {error_json['error']}")
                    except json.JSONDecodeError:
                        pass
                    raise ValueError(f"API 请求失败 ({response.status_code}): {error_detail[:500]}")
                
                result = response.json()
                logger.info(f"[VisionService] DashScope Image Generation Response - Status: {response.status_code}, Response: {json.dumps(result, ensure_ascii=False)[:2000]}")
                
                output = result.get("output", {})
                choices = output.get("choices", [])
                images = []
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", [])
                    for item in content:
                        if isinstance(item, dict) and "image" in item:
                            images.append(item["image"])
                
                return {
                    "images": images,
                    "raw": result,
                    "usage": result.get("usage", {}),
                    "request_id": result.get("request_id", ""),
                }
        except httpx.ConnectError:
            raise ValueError(f"无法连接到 API 服务器: {url}，请检查网络或配置代理")
        except httpx.TimeoutException:
            raise ValueError("请求超时，请检查网络连接")

    def _get_headers(self, api_key: str, call_method: str) -> dict:
        if call_method == "messages":
            return {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _build_multimodal_content(
        self,
        text: str,
        image_url: str,
        call_method: str,
    ) -> list:
        if call_method == "messages":
            return self._build_anthropic_content(text, image_url)
        elif call_method == "dashscope":
            return self._build_dashscope_content(text, image_url)
        else:
            return self._build_openai_content(text, image_url)

    def _build_openai_content(self, text: str, image_url: str) -> list[dict]:
        content: list[dict] = []
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        content.append({"type": "text", "text": text})
        return content

    def _build_anthropic_content(self, text: str, image_url: str) -> list[dict]:
        content: list[dict] = []
        if image_url:
            if image_url.startswith("data:"):
                media_type, data = self._parse_data_url(image_url)
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data,
                    }
                })
            else:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": image_url,
                    }
                })
        content.append({"type": "text", "text": text})
        return content

    def _build_dashscope_content(self, text: str, image_url: str) -> list[dict]:
        content: list[dict] = []
        if image_url:
            content.append({"image": image_url})
        content.append({"text": text})
        return content

    def _parse_data_url(self, data_url: str) -> tuple:
        if data_url.startswith("data:"):
            header, data = data_url.split(",", 1)
            media_type = header.split(":")[1].split(";")[0]
            return media_type, data
        return "image/png", data_url

    def _format_messages_with_image(
        self,
        messages: list,
        image_url: str,
        call_method: str,
    ) -> list[dict]:
        formatted = []
        for i, m in enumerate(messages):
            if hasattr(m, 'model_dump'):
                msg = m.model_dump()
            elif isinstance(m, dict):
                msg = m
            else:
                msg = {"role": getattr(m, 'role', 'user'), "content": getattr(m, 'content', '')}
            
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if i == len(messages) - 1 and role == "user" and image_url:
                multimodal_content = self._build_multimodal_content(
                    text=content,
                    image_url=image_url,
                    call_method=call_method,
                )
                formatted.append({"role": role, "content": multimodal_content})
            else:
                formatted.append({"role": role, "content": content})
        
        return formatted

    async def image_understanding(
        self,
        messages: list,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        image_url: str = "",
        **kwargs,
    ) -> dict:
        if not api_key:
            raise ValueError("API Key 未配置，请在模型配置中设置 API Key")

        logger.info(f"[VisionService] image_understanding kwargs: {kwargs}, image_url: {image_url[:100] if image_url else 'None'}")

        formatted = self._format_messages_with_image(messages, image_url, call_method)
        
        return await self.text_service.chat(
            messages=formatted,
            model=model,
            call_method=call_method,
            api_key=api_key,
            url=url,
            **kwargs,
        )

    async def stream_image_understanding(
        self,
        messages: list,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        image_url: str = "",
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        if not api_key:
            yield f"data: {json.dumps({'error': 'API Key 未配置，请在模型配置中设置 API Key'})}\n\n"
            return

        formatted = self._format_messages_with_image(messages, image_url, call_method)
        
        async for chunk in self.text_service.stream_chat(
            messages=formatted,
            model=model,
            call_method=call_method,
            api_key=api_key,
            url=url,
            **kwargs,
        ):
            yield chunk
