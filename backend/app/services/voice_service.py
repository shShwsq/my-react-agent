import asyncio
import base64
import json
import logging
import uuid
from typing import AsyncGenerator

import httpx
import websockets
from websockets.exceptions import InvalidStatus, WebSocketException

logger = logging.getLogger(__name__)


def detect_audio_mime(base64_data: str) -> str:
    try:
        header_bytes = base64.b64decode(base64_data[:32])
    except Exception:
        return "audio/wav"
    
    if len(header_bytes) < 4:
        return "audio/wav"
    
    header = header_bytes[:12]
    
    if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
        return "audio/wav"
    if header[:3] == b'ID3' or (header[0] == 0xFF and header[1] & 0xE0 == 0xE0):
        return "audio/mpeg"
    if header[:4] == b'fLaC':
        return "audio/flac"
    if header[:4] == b'OggS':
        return "audio/ogg"
    if header[:4] == b'ftyp':
        return "audio/mp4"
    
    return "audio/wav"


class VoiceService:
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

    async def asr(
        self,
        audio_data: str,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        **kwargs,
    ) -> dict:
        if not api_key:
            raise ValueError("API Key 未配置，请在模型配置中设置 API Key")

        logger.info(f"[VoiceService] asr kwargs: {kwargs}")

        if audio_data.startswith("data:"):
            audio_data = audio_data.split(",", 1)[1]

        if call_method == "dashscope":
            return await self._dashscope_asr(audio_data, model, api_key, url, **kwargs)
        else:
            return await self._openai_asr(audio_data, model, api_key, url, **kwargs)

    async def stream_asr(
        self,
        audio_data: str,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        if not api_key:
            yield f"data: {json.dumps({'error': 'API Key 未配置，请在模型配置中设置 API Key'})}\n\n"
            return

        logger.info(f"[VoiceService] stream_asr kwargs: {kwargs}")

        if audio_data.startswith("data:"):
            audio_data = audio_data.split(",", 1)[1]

        async for chunk in self._stream_openai_asr(audio_data, model, api_key, url, **kwargs):
            yield chunk

    async def _stream_openai_asr(
        self,
        audio_data: str,
        model: str,
        api_key: str,
        url: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        if audio_data.startswith("http://") or audio_data.startswith("https://"):
            audio_url = audio_data
        else:
            mime_type = detect_audio_mime(audio_data)
            audio_url = f"data:{mime_type};base64,{audio_data}"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_url
                            }
                        }
                    ],
                    "role": "user"
                }
            ],
            "stream": True,
            "asr_options": {
                "enable_itn": False
            }
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        logger.info(f"[VoiceService] Stream OpenAI ASR Request - URL: {url}, Model: {model}")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 401:
                        logger.error(f"[VoiceService] Stream OpenAI ASR Error - Status: 401, Response: API Key 无效或已过期")
                        yield f"data: {json.dumps({'error': 'API Key 无效或已过期'})}\n\n"
                        return
                    if response.status_code == 404:
                        logger.error(f"[VoiceService] Stream OpenAI ASR Error - Status: 404, Response: API 端点不存在")
                        yield f"data: {json.dumps({'error': f'API 端点不存在，请检查 URL: {url}'})}\n\n"
                        return
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            logger.info(f"[VoiceService] Stream OpenAI ASR Raw Response: {data[:500]}")
                            try:
                                chunk = json.loads(data)
                                choices = chunk.get("choices", [])
                                if not choices:
                                    continue
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except json.JSONDecodeError:
                                continue
                    logger.info(f"[VoiceService] Stream OpenAI ASR Response - Completed")
                    yield "data: [DONE]\n\n"
        except httpx.ConnectError as e:
            logger.error(f"[VoiceService] Stream OpenAI ASR Error - ConnectError: {e}")
            yield f"data: {json.dumps({'error': f'无法连接到 API 服务器: {url}，请检查网络或配置代理'})}\n\n"
        except httpx.TimeoutException as e:
            logger.error(f"[VoiceService] Stream OpenAI ASR Error - TimeoutException: {e}")
            yield f"data: {json.dumps({'error': '请求超时，请检查网络连接'})}\n\n"

    async def _openai_asr(
        self,
        audio_data: str,
        model: str,
        api_key: str,
        url: str,
        **kwargs,
    ) -> dict:
        if audio_data.startswith("http://") or audio_data.startswith("https://"):
            audio_url = audio_data
        else:
            mime_type = detect_audio_mime(audio_data)
            audio_url = f"data:{mime_type};base64,{audio_data}"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_url
                            }
                        }
                    ],
                    "role": "user"
                }
            ],
            "stream": False,
            "asr_options": {
                "enable_itn": False
            }
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        logger.info(f"[VoiceService] OpenAI ASR Request - URL: {url}, Model: {model}")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 401:
                    raise ValueError("API Key 无效或已过期")
                if response.status_code == 404:
                    raise ValueError(f"API 端点不存在，请检查 URL: {url}")
                
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"[VoiceService] OpenAI ASR Error - Status: {response.status_code}, Response: {error_detail}")
                    try:
                        error_json = response.json()
                        if "error" in error_json and "message" in error_json["error"]:
                            raise ValueError(f"API 错误: {error_json['error']['message']}")
                        elif "message" in error_json:
                            raise ValueError(f"API 错误: {error_json['message']}")
                    except json.JSONDecodeError:
                        pass
                    raise ValueError(f"API 请求失败 ({response.status_code}): {error_detail[:500]}")
                
                result = response.json()
                logger.info(f"[VoiceService] OpenAI ASR Response - Status: {response.status_code}, Response: {json.dumps(result, ensure_ascii=False)[:2000]}")
                
                content = ""
                choices = result.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    message_content = message.get("content")
                    if isinstance(message_content, str):
                        content = message_content
                    elif isinstance(message_content, list) and len(message_content) > 0:
                        content = message_content[0].get("text", "")
                if not content:
                    content = result.get("text", "")
                return {"content": content, "raw": result}
        except httpx.ConnectError:
            raise ValueError(f"无法连接到 API 服务器: {url}，请检查网络或配置代理")
        except httpx.TimeoutException:
            raise ValueError("请求超时，请检查网络连接")

    async def _dashscope_asr(
        self,
        audio_data: str,
        model: str,
        api_key: str,
        url: str,
        **kwargs,
    ) -> dict:
        if audio_data.startswith("http://") or audio_data.startswith("https://"):
            audio_url = audio_data
        else:
            mime_type = detect_audio_mime(audio_data)
            audio_url = f"data:{mime_type};base64,{audio_data}"
        
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "content": [
                            {
                                "text": ""
                            }
                        ],
                        "role": "system"
                    },
                    {
                        "content": [
                            {
                                "audio": audio_url
                            }
                        ],
                        "role": "user"
                    }
                ]
            },
            "parameters": {
                "asr_options": {
                    "enable_itn": False
                }
            }
        }
        logger.info(f"[VoiceService] DashScope ASR Request - URL: {url}, Model: {model}")
        logger.info(f"[VoiceService] DashScope ASR Payload - audio_url type: {'URL' if audio_url.startswith('http') else 'Base64'}, audio_url preview: {audio_url[:100]}...")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self._get_headers(api_key, "dashscope"), json=payload)
                if response.status_code == 401:
                    raise ValueError("API Key 无效或已过期")
                if response.status_code == 404:
                    raise ValueError(f"API 端点不存在，请检查 URL: {url}")
                
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"[VoiceService] DashScope ASR Error - Status: {response.status_code}, Response: {error_detail}")
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
                logger.info(f"[VoiceService] DashScope ASR Response - Status: {response.status_code}, Response: {json.dumps(result, ensure_ascii=False)[:2000]}")
                
                content = ""
                output = result.get("output", {})
                if isinstance(output, dict):
                    choices = output.get("choices", [])
                    if choices and len(choices) > 0:
                        message = choices[0].get("message", {})
                        message_content = message.get("content", [])
                        if message_content and len(message_content) > 0:
                            content = message_content[0].get("text", "")
                    if not content:
                        content = output.get("text", "") or output.get("sentence", {}).get("text", "")
                return {"content": content, "raw": result}
        except httpx.ConnectError:
            raise ValueError(f"无法连接到 API 服务器: {url}，请检查网络或配置代理")
        except httpx.TimeoutException:
            raise ValueError("请求超时，请检查网络连接")

    async def tts(
        self,
        text: str,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        voice: str = "longanyang",
        audio_format: str = "mp3",
        sample_rate: int = 22050,
        **kwargs,
    ) -> dict:
        if not api_key:
            raise ValueError("API Key 未配置，请在模型配置中设置 API Key")

        logger.info(f"[VoiceService] tts kwargs: {kwargs}")

        if call_method == "websocket":
            return await self._wss_tts(text, model, api_key, url, voice, audio_format, sample_rate, **kwargs)
        else:
            raise ValueError(f"不支持的调用方法: {call_method}")

    async def _wss_tts(
        self,
        text: str,
        model: str,
        api_key: str,
        url: str,
        voice: str,
        audio_format: str,
        sample_rate: int,
        **kwargs,
    ) -> dict:
        logger.info(f"[VoiceService] WSS TTS Request - URL: {url}, Model: {model}, Voice: {voice}, Text: {text[:100]}")

        task_id = str(uuid.uuid4())
        
        run_task = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "model": model,
                "parameters": {
                    "text_type": "PlainText",
                    "voice": voice,
                    "format": audio_format,
                    "sample_rate": sample_rate,
                    "volume": 50,
                    "rate": 1,
                    "pitch": 1
                },
                "input": {}
            }
        }
        logger.info(f"[VoiceService] WSS TTS run_task: {json.dumps(run_task, ensure_ascii=False)}")
        
        continue_task = {
            "header": {
                "action": "continue-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "input": {
                    "text": text
                }
            }
        }
        
        finish_task = {
            "header": {
                "action": "finish-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "input": {}
            }
        }
        
        headers = {
            "Authorization": f"bearer {api_key}"
        }
        
        audio_chunks = []
        
        try:
            async with websockets.connect(url, additional_headers=headers, ping_interval=None) as ws:
                await ws.send(json.dumps(run_task))
                
                task_started = False
                task_finished = False
                
                while not task_finished:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=120.0)
                    except asyncio.TimeoutError:
                        raise ValueError("WebSocket 接收超时")
                    
                    if isinstance(message, bytes):
                        audio_chunks.append(message)
                    else:
                        event = json.loads(message)
                        event_name = event.get("header", {}).get("event")
                        logger.info(f"[VoiceService] WSS TTS Event: {event_name}, Payload: {json.dumps(event, ensure_ascii=False)[:500]}")
                        
                        if event_name == "task-started":
                            task_started = True
                            await ws.send(json.dumps(continue_task))
                            await ws.send(json.dumps(finish_task))
                        elif event_name == "task-finished":
                            task_finished = True
                        elif event_name == "task-failed":
                            error_payload = event.get("payload", {})
                            error_msg = error_payload.get("message") or error_payload.get("error") or json.dumps(error_payload, ensure_ascii=False)
                            raise ValueError(f"TTS 任务失败: {error_msg}")
            
            audio_data = b"".join(audio_chunks)
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            result = {
                "audio": audio_base64,
                "format": audio_format,
            }
            logger.info(f"[VoiceService] WSS TTS Response - Audio length: {len(audio_base64)}")
            return result
            
        except InvalidStatus as e:
            if e.response.status_code == 401:
                raise ValueError("API Key 无效或已过期")
            raise ValueError(f"WebSocket 连接失败: {e}")
        except WebSocketException as e:
            raise ValueError(f"WebSocket 错误: {e}")

    async def stream_tts(
        self,
        text: str,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        voice: str = "longanyang",
        audio_format: str = "mp3",
        sample_rate: int = 22050,
        **kwargs,
    ) -> AsyncGenerator[bytes, None]:
        if not api_key:
            yield json.dumps({"error": "API Key 未配置，请在模型配置中设置 API Key"}).encode()
            return

        if call_method == "websocket":
            async for chunk in self._stream_wss_tts(text, model, api_key, url, voice, audio_format, sample_rate, **kwargs):
                yield chunk
        else:
            yield json.dumps({"error": f"不支持的调用方法: {call_method}"}).encode()

    async def _stream_wss_tts(
        self,
        text: str,
        model: str,
        api_key: str,
        url: str,
        voice: str,
        audio_format: str,
        sample_rate: int,
        **kwargs,
    ) -> AsyncGenerator[bytes, None]:
        logger.info(f"[VoiceService] Stream WSS TTS Request - URL: {url}, Model: {model}, Voice: {voice}, Text: {text[:100]}")

        task_id = str(uuid.uuid4())
        
        run_task = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "model": model,
                "parameters": {
                    "text_type": "PlainText",
                    "voice": voice,
                    "format": audio_format,
                    "sample_rate": sample_rate,
                    "volume": 50,
                    "rate": 1,
                    "pitch": 1
                },
                "input": {}
            }
        }
        
        continue_task = {
            "header": {
                "action": "continue-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "input": {
                    "text": text
                }
            }
        }
        
        finish_task = {
            "header": {
                "action": "finish-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "input": {}
            }
        }
        
        headers = {
            "Authorization": f"bearer {api_key}"
        }
        
        try:
            async with websockets.connect(url, additional_headers=headers, ping_interval=None) as ws:
                await ws.send(json.dumps(run_task))
                
                task_started = False
                task_finished = False
                
                while not task_finished:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=120.0)
                    except asyncio.TimeoutError:
                        yield json.dumps({"error": "WebSocket 接收超时"}).encode()
                        return
                    
                    if isinstance(message, bytes):
                        yield message
                    else:
                        event = json.loads(message)
                        event_name = event.get("header", {}).get("event")
                        logger.info(f"[VoiceService] Stream WSS TTS Event: {event_name}, Payload: {json.dumps(event, ensure_ascii=False)[:500]}")
                        
                        if event_name == "task-started":
                            task_started = True
                            await ws.send(json.dumps(continue_task))
                            await ws.send(json.dumps(finish_task))
                        elif event_name == "task-finished":
                            task_finished = True
                        elif event_name == "task-failed":
                            error_payload = event.get("payload", {})
                            error_msg = error_payload.get("message") or error_payload.get("error") or json.dumps(error_payload, ensure_ascii=False)
                            yield json.dumps({"error": f"TTS 任务失败: {error_msg}"}).encode()
                            return
                            
        except InvalidStatus as e:
            if e.response.status_code == 401:
                yield json.dumps({"error": "API Key 无效或已过期"}).encode()
            else:
                yield json.dumps({"error": f"WebSocket 连接失败: {e}"}).encode()
        except WebSocketException as e:
            yield json.dumps({"error": f"WebSocket 错误: {e}"}).encode()
