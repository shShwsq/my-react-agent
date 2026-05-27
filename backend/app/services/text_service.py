import json
import logging
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)


class TextService:
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

    def _format_messages(self, messages: list) -> list[dict]:
        formatted = []
        for m in messages:
            if hasattr(m, 'role'):
                formatted.append({"role": m.role, "content": m.content})
            else:
                formatted.append(m)
        return formatted

    def _extract_system_for_anthropic(self, messages: list[dict]) -> tuple[str, list[dict]]:
        system_content = ""
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
            else:
                filtered_messages.append(msg)
        return system_content, filtered_messages

    def _convert_tools_to_anthropic(self, tools: list[dict]) -> list[dict]:
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tool = {
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}})
                }
                anthropic_tools.append(anthropic_tool)
        return anthropic_tools

    def _convert_tools_for_responses(self, tools: list[dict]) -> list[dict]:
        responses_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                responses_tool = {
                    "type": "function",
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {"type": "object", "properties": {}})
                }
                responses_tools.append(responses_tool)
        return responses_tools

    def _convert_tool_choice_for_responses(self, tool_choice: dict) -> dict:
        if isinstance(tool_choice, str):
            return tool_choice
        if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            func_name = tool_choice.get("function", {}).get("name", "")
            return {
                "mode": "required",
                "type": "allowed_tools",
                "tools": [{"type": "function", "name": func_name}]
            }
        return tool_choice

    async def chat(
        self,
        messages: list,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        **kwargs,
    ) -> dict:
        if not api_key:
            raise ValueError("API Key 未配置，请在模型配置中设置 API Key")

        kwargs.setdefault("enable_thinking", False)
        logger.info(f"[TextService] chat kwargs: {kwargs}")

        formatted = self._format_messages(messages)

        if call_method == "messages":
            return await self._anthropic_chat(formatted, model, api_key, url, **kwargs)
        elif call_method == "dashscope":
            return await self._dashscope_chat(formatted, model, api_key, url, **kwargs)
        elif call_method == "responses":
            return await self._openai_responses(formatted, model, api_key, url, **kwargs)
        else:
            return await self._openai_chat(formatted, model, api_key, url, **kwargs)

    async def _openai_chat(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> dict:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            payload["enable_thinking"] = enable_thinking
        
        tools = kwargs.get("tools")
        if tools:
            payload["tools"] = tools
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            payload["tool_choice"] = tool_choice
        logger.info(f"[TextService] OpenAI Chat Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self._get_headers(api_key, "chat"), json=payload)
                if response.status_code == 401:
                    raise ValueError("API Key 无效或已过期")
                if response.status_code == 404:
                    raise ValueError(f"API 端点不存在，请检查 URL: {url}")
                
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"[TextService] OpenAI Chat Error - Status: {response.status_code}, Response: {error_detail}")
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
                logger.info(f"[TextService] OpenAI Chat Response - Status: {response.status_code}, Response: {json.dumps(result, ensure_ascii=False)[:2000]}")
                
                message = result.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                return {
                    "content": content,
                    "tool_calls": tool_calls,
                    "raw": result
                }
        except httpx.ConnectError:
            raise ValueError(f"无法连接到 API 服务器: {url}，请检查网络或配置代理")
        except httpx.TimeoutException:
            raise ValueError("请求超时，请检查网络连接")

    async def _openai_responses(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> dict:
        input_items = []
        for msg in messages:
            input_items.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        payload = {
            "model": model,
            "input": input_items,
        }
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            payload["reasoning"] = {"effort": "medium"} if enable_thinking else {"effort": "none"}
        
        tools = kwargs.get("tools")
        if tools:
            payload["tools"] = self._convert_tools_for_responses(tools)
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            payload["tool_choice"] = self._convert_tool_choice_for_responses(tool_choice)
        
        logger.info(f"[TextService] OpenAI Responses Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self._get_headers(api_key, "chat"), json=payload)
                if response.status_code == 401:
                    raise ValueError("API Key 无效或已过期")
                if response.status_code == 404:
                    raise ValueError(f"API 端点不存在，请检查 URL: {url}")
                
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"[TextService] OpenAI Responses Error - Status: {response.status_code}, Response: {error_detail}")
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
                logger.info(f"[TextService] OpenAI Responses Response - Status: {response.status_code}, Response: {json.dumps(result, ensure_ascii=False)[:2000]}")
                
                content = ""
                tool_calls = []
                output = result.get("output", [])
                if output:
                    content_list = output[0].get("content", [])
                    if content_list:
                        content = content_list[0].get("text", "")
                    tool_calls = output[0].get("tool_calls", [])
                return {"content": content, "tool_calls": tool_calls, "raw": result}
        except httpx.ConnectError:
            raise ValueError(f"无法连接到 API 服务器: {url}，请检查网络或配置代理")
        except httpx.TimeoutException:
            raise ValueError("请求超时，请检查网络连接")

    async def _anthropic_chat(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> dict:
        system_content, filtered_messages = self._extract_system_for_anthropic(messages)
        payload = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": 4096,
        }
        if system_content:
            payload["system"] = system_content
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            payload["thinking"] = {"type": "enabled" if enable_thinking else "disabled", "budget_tokens": 1024}
        
        tools = kwargs.get("tools")
        if tools:
            anthropic_tools = self._convert_tools_to_anthropic(tools)
            if anthropic_tools:
                payload["tools"] = anthropic_tools
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
                payload["tool_choice"] = {"type": "tool", "name": tool_choice["function"]["name"]}
            elif tool_choice == "auto":
                payload["tool_choice"] = {"type": "auto"}
            elif tool_choice == "any":
                payload["tool_choice"] = {"type": "any"}
        
        logger.info(f"[TextService] Anthropic Chat Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self._get_headers(api_key, "messages"), json=payload)
                if response.status_code == 401:
                    raise ValueError("API Key 无效或已过期")
                if response.status_code == 404:
                    raise ValueError(f"API 端点不存在，请检查 URL: {url}")
                
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"[TextService] Anthropic Chat Error - Status: {response.status_code}, Response: {error_detail}")
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
                logger.info(f"[TextService] Anthropic Chat Response - Status: {response.status_code}, Response: {json.dumps(result, ensure_ascii=False)[:2000]}")
                
                content = ""
                tool_calls = []
                content_list = result.get("content", [])
                if content_list:
                    for item in content_list:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text = item.get("text", "")
                                if text:
                                    content += text
                            elif item.get("type") == "tool_use":
                                tool_calls.append({
                                    "id": item.get("id", ""),
                                    "type": "function",
                                    "function": {
                                        "name": item.get("name", ""),
                                        "arguments": json.dumps(item.get("input", {}))
                                    }
                                })
                return {"content": content, "tool_calls": tool_calls, "raw": result}
        except httpx.ConnectError:
            raise ValueError(f"无法连接到 API 服务器: {url}，请检查网络或配置代理")
        except httpx.TimeoutException:
            raise ValueError("请求超时，请检查网络连接")

    async def _dashscope_chat(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> dict:
        input_content = []
        for msg in messages:
            input_content.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        payload = {
            "model": model,
            "input": {
                "messages": input_content,
            },
        }
        parameters = {}
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            parameters["enable_thinking"] = enable_thinking
        
        tools = kwargs.get("tools")
        if tools:
            parameters["tools"] = tools
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
                parameters["tool_choice"] = {"type": "function", "function": {"name": tool_choice["function"]["name"]}}
            else:
                parameters["tool_choice"] = tool_choice
        
        if parameters:
            payload["parameters"] = parameters
        
        logger.info(f"[TextService] DashScope Chat Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=self._get_headers(api_key, "dashscope"), json=payload)
                if response.status_code == 401:
                    raise ValueError("API Key 无效或已过期")
                if response.status_code == 404:
                    raise ValueError(f"API 端点不存在，请检查 URL: {url}")
                
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"[TextService] DashScope Chat Error - Status: {response.status_code}, Response: {error_detail}")
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
                logger.info(f"[TextService] DashScope Chat Response - Status: {response.status_code}, Response: {json.dumps(result, ensure_ascii=False)[:2000]}")
                
                content = ""
                tool_calls = []
                output = result.get("output", {})
                if isinstance(output, dict):
                    content = output.get("text", "")
                    if not content:
                        choices = output.get("choices", [])
                        if choices:
                            message = choices[0].get("message", {})
                            msg_content = message.get("content", "")
                            if isinstance(msg_content, list):
                                for item in msg_content:
                                    if isinstance(item, dict) and "text" in item:
                                        content += item.get("text", "")
                            else:
                                content = msg_content if isinstance(msg_content, str) else ""
                            tc = message.get("tool_calls", [])
                            if tc:
                                tool_calls = tc
                return {"content": content, "tool_calls": tool_calls, "raw": result}
        except httpx.ConnectError:
            raise ValueError(f"无法连接到 API 服务器: {url}，请检查网络或配置代理")
        except httpx.TimeoutException:
            raise ValueError("请求超时，请检查网络连接")

    async def stream_chat(
        self,
        messages: list,
        model: str,
        call_method: str,
        api_key: str,
        url: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        if not api_key:
            yield f"data: {json.dumps({'error': 'API Key 未配置，请在模型配置中设置 API Key'})}\n\n"
            return

        kwargs.setdefault("enable_thinking", False)
        formatted = self._format_messages(messages)

        if call_method == "messages":
            async for chunk in self._stream_anthropic(formatted, model, api_key, url, **kwargs):
                yield chunk
        elif call_method == "dashscope":
            async for chunk in self._stream_dashscope(formatted, model, api_key, url, **kwargs):
                yield chunk
        elif call_method == "responses":
            async for chunk in self._stream_openai_responses(formatted, model, api_key, url, **kwargs):
                yield chunk
        else:
            async for chunk in self._stream_openai_chat(formatted, model, api_key, url, **kwargs):
                yield chunk

    async def _stream_openai_chat(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> AsyncGenerator[str, None]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            payload["enable_thinking"] = enable_thinking
        
        tools = kwargs.get("tools")
        if tools:
            payload["tools"] = tools
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            payload["tool_choice"] = tool_choice
        
        logger.info(f"[TextService] Stream OpenAI Chat Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=self._get_headers(api_key, "chat"), json=payload) as response:
                    if response.status_code == 401:
                        logger.error(f"[TextService] Stream OpenAI Chat Error - Status: 401, Response: API Key 无效或已过期")
                        yield f"data: {json.dumps({'error': 'API Key 无效或已过期'})}\n\n"
                        return
                    if response.status_code == 404:
                        logger.error(f"[TextService] Stream OpenAI Chat Error - Status: 404, Response: API 端点不存在")
                        yield f"data: {json.dumps({'error': f'API 端点不存在，请检查 URL: {url}'})}\n\n"
                        return
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            logger.info(f"[TextService] Stream OpenAI Chat Raw Response: {data[:500]}")
                            try:
                                chunk = json.loads(data)
                                choices = chunk.get("choices", [])
                                if not choices:
                                    continue
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                tool_calls = delta.get("tool_calls", [])
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                                if tool_calls:
                                    yield f"data: {json.dumps({'tool_calls': tool_calls})}\n\n"
                            except json.JSONDecodeError:
                                continue
                    logger.info(f"[TextService] Stream OpenAI Chat Response - Completed")
                    yield "data: [DONE]\n\n"
        except httpx.ConnectError as e:
            logger.error(f"[TextService] Stream OpenAI Chat Error - ConnectError: {e}")
            yield f"data: {json.dumps({'error': f'无法连接到 API 服务器: {url}，请检查网络或配置代理'})}\n\n"
        except httpx.TimeoutException as e:
            logger.error(f"[TextService] Stream OpenAI Chat Error - TimeoutException: {e}")
            yield f"data: {json.dumps({'error': '请求超时，请检查网络连接'})}\n\n"

    async def _stream_openai_responses(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> AsyncGenerator[str, None]:
        input_items = []
        for msg in messages:
            input_items.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        payload = {
            "model": model,
            "input": input_items,
            "stream": True,
        }
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            payload["reasoning"] = {"effort": "medium"} if enable_thinking else {"effort": "none"}
        
        tools = kwargs.get("tools")
        if tools:
            payload["tools"] = self._convert_tools_for_responses(tools)
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            payload["tool_choice"] = self._convert_tool_choice_for_responses(tool_choice)
        
        logger.info(f"[TextService] Stream OpenAI Responses Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=self._get_headers(api_key, "chat"), json=payload) as response:
                    if response.status_code == 401:
                        logger.error(f"[TextService] Stream OpenAI Responses Error - Status: 401, Response: API Key 无效或已过期")
                        yield f"data: {json.dumps({'error': 'API Key 无效或已过期'})}\n\n"
                        return
                    if response.status_code == 404:
                        logger.error(f"[TextService] Stream OpenAI Responses Error - Status: 404, Response: API 端点不存在")
                        yield f"data: {json.dumps({'error': f'API 端点不存在，请检查 URL: {url}'})}\n\n"
                        return
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("event:"):
                            continue
                        if line.startswith("data:"):
                            data = line[5:].lstrip()
                        else:
                            continue
                        if data == "[DONE]":
                            break
                        logger.info(f"[TextService] Stream OpenAI Responses Raw Response: {data[:500]}")
                        try:
                            event = json.loads(data)
                            event_type = event.get("type", "")
                            if event_type == "response.output_text.delta":
                                delta = event.get("delta", "")
                                if delta:
                                    yield f"data: {json.dumps({'content': delta})}\n\n"
                            elif event_type == "response.function_call_arguments.delta":
                                delta = event.get("delta", "")
                                if delta:
                                    yield f"data: {json.dumps({'tool_calls': [{'function': {'arguments': delta}}]})}\n\n"
                            elif event_type == "response.output_item.added":
                                item = event.get("item", {})
                                if item.get("type") == "function_call":
                                    tool_call = {
                                        "id": item.get("id", ""),
                                        "type": "function",
                                        "function": {
                                            "name": item.get("name", ""),
                                            "arguments": ""
                                        }
                                    }
                                    yield f"data: {json.dumps({'tool_calls': [tool_call]})}\n\n"
                            elif event_type == "response.completed":
                                break
                        except json.JSONDecodeError:
                            continue
                    logger.info(f"[TextService] Stream OpenAI Responses Response - Completed")
                    yield "data: [DONE]\n\n"
        except httpx.ConnectError as e:
            logger.error(f"[TextService] Stream OpenAI Responses Error - ConnectError: {e}")
            yield f"data: {json.dumps({'error': f'无法连接到 API 服务器: {url}，请检查网络或配置代理'})}\n\n"
        except httpx.TimeoutException as e:
            logger.error(f"[TextService] Stream OpenAI Responses Error - TimeoutException: {e}")
            yield f"data: {json.dumps({'error': '请求超时，请检查网络连接'})}\n\n"

    async def _stream_anthropic(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> AsyncGenerator[str, None]:
        system_content, filtered_messages = self._extract_system_for_anthropic(messages)
        payload = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": 4096,
            "stream": True,
        }
        if system_content:
            payload["system"] = system_content
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            payload["thinking"] = {"type": "enabled" if enable_thinking else "disabled", "budget_tokens": 1024}
        
        tools = kwargs.get("tools")
        if tools:
            anthropic_tools = self._convert_tools_to_anthropic(tools)
            if anthropic_tools:
                payload["tools"] = anthropic_tools
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
                payload["tool_choice"] = {"type": "tool", "name": tool_choice["function"]["name"]}
            elif tool_choice == "auto":
                payload["tool_choice"] = {"type": "auto"}
            elif tool_choice == "any":
                payload["tool_choice"] = {"type": "any"}
        
        logger.info(f"[TextService] Stream Anthropic Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=self._get_headers(api_key, "messages"), json=payload) as response:
                    if response.status_code == 401:
                        logger.error(f"[TextService] Stream Anthropic Error - Status: 401, Response: API Key 无效或已过期")
                        yield f"data: {json.dumps({'error': 'API Key 无效或已过期'})}\n\n"
                        return
                    if response.status_code == 404:
                        logger.error(f"[TextService] Stream Anthropic Error - Status: 404, Response: API 端点不存在")
                        yield f"data: {json.dumps({'error': f'API 端点不存在，请检查 URL: {url}'})}\n\n"
                        return
                    if response.status_code >= 400:
                        error_body = await response.aread()
                        error_detail = error_body.decode('utf-8')
                        logger.error(f"[TextService] Stream Anthropic Error - Status: {response.status_code}, Response: {error_detail}")
                        try:
                            error_json = json.loads(error_detail)
                            if "error" in error_json:
                                err_msg = error_json["error"].get("message", error_detail)
                            elif "message" in error_json:
                                err_msg = error_json["message"]
                            else:
                                err_msg = error_detail[:500]
                        except json.JSONDecodeError:
                            err_msg = error_detail[:500]
                        yield f"data: {json.dumps({'error': f'API 请求失败 ({response.status_code}): {err_msg}'})}\n\n"
                        return
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("event:"):
                            continue
                        if line.startswith("data:"):
                            line = line[5:].lstrip()
                        logger.info(f"[TextService] Stream Anthropic Raw Response: {line[:500]}")
                        try:
                            event = json.loads(line)
                            event_type = event.get("type", "")
                            
                            if event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                delta_type = delta.get("type", "")
                                
                                if delta_type == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield f"data: {json.dumps({'content': text})}\n\n"
                                elif delta_type == "thinking_delta":
                                    thinking = delta.get("thinking", "")
                                    if thinking:
                                        yield f"data: {json.dumps({'thinking': thinking})}\n\n"
                                elif delta_type == "input_json_delta":
                                    partial_json = delta.get("partial_json", "")
                                    if partial_json:
                                        yield f"data: {json.dumps({'tool_calls': [{'function': {'arguments': partial_json}}]})}\n\n"
                            
                            elif event_type == "content_block_start":
                                block = event.get("content_block", {})
                                block_type = block.get("type", "")
                                if block_type == "tool_use":
                                    tool_call = {
                                        "id": block.get("id", ""),
                                        "type": "function",
                                        "function": {
                                            "name": block.get("name", ""),
                                            "arguments": ""
                                        }
                                    }
                                    yield f"data: {json.dumps({'tool_calls': [tool_call]})}\n\n"
                                        
                            elif event_type == "message_stop":
                                break
                                
                        except json.JSONDecodeError:
                            continue
                    logger.info(f"[TextService] Stream Anthropic Response - Completed")
                    yield "data: [DONE]\n\n"
        except httpx.ConnectError as e:
            logger.error(f"[TextService] Stream Anthropic Error - ConnectError: {e}")
            yield f"data: {json.dumps({'error': f'无法连接到 API 服务器: {url}，请检查网络或配置代理'})}\n\n"
        except httpx.TimeoutException as e:
            logger.error(f"[TextService] Stream Anthropic Error - TimeoutException: {e}")
            yield f"data: {json.dumps({'error': '请求超时，请检查网络连接'})}\n\n"

    async def _stream_dashscope(self, messages: list[dict], model: str, api_key: str, url: str, **kwargs) -> AsyncGenerator[str, None]:
        input_content = []
        for msg in messages:
            input_content.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        payload = {
            "model": model,
            "input": {
                "messages": input_content,
            },
            "parameters": {
                "incremental_output": True,
                "result_format": "message",
            },
        }
        enable_thinking = kwargs.get("enable_thinking")
        if enable_thinking is not None:
            payload["parameters"]["enable_thinking"] = enable_thinking
        
        tools = kwargs.get("tools")
        if tools:
            payload["parameters"]["tools"] = tools
        
        tool_choice = kwargs.get("tool_choice")
        if tool_choice:
            if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
                payload["parameters"]["tool_choice"] = {"type": "function", "function": {"name": tool_choice["function"]["name"]}}
            else:
                payload["parameters"]["tool_choice"] = tool_choice
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable",
        }
        logger.info(f"[TextService] Stream DashScope Request - URL: {url}, Model: {model}, Payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 401:
                        logger.error(f"[TextService] Stream DashScope Error - Status: 401, Response: API Key 无效或已过期")
                        yield f"data: {json.dumps({'error': 'API Key 无效或已过期'})}\n\n"
                        return
                    if response.status_code == 404:
                        logger.error(f"[TextService] Stream DashScope Error - Status: 404, Response: API 端点不存在")
                        yield f"data: {json.dumps({'error': f'API 端点不存在，请检查 URL: {url}'})}\n\n"
                        return
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            data = line[5:].strip()
                            if not data:
                                continue
                            logger.info(f"[TextService] Stream DashScope Raw Response: {data[:500]}")
                            try:
                                result = json.loads(data)
                                output = result.get("output", {})
                                choices = output.get("choices", [])
                                if choices:
                                    message = choices[0].get("message", {})
                                    content = message.get("content", "")
                                    reasoning_content = message.get("reasoning_content", "")
                                    tool_calls = message.get("tool_calls", [])
                                    
                                    if content:
                                        if isinstance(content, list):
                                            for item in content:
                                                if isinstance(item, dict) and "text" in item:
                                                    text = item.get("text", "")
                                                    if text:
                                                        yield f"data: {json.dumps({'content': text})}\n\n"
                                        elif isinstance(content, str):
                                            yield f"data: {json.dumps({'content': content})}\n\n"
                                    
                                    if reasoning_content:
                                        yield f"data: {json.dumps({'thinking': reasoning_content})}\n\n"
                                    
                                    if tool_calls:
                                        yield f"data: {json.dumps({'tool_calls': tool_calls})}\n\n"
                                else:
                                    text = output.get("text", "")
                                    if text:
                                        yield f"data: {json.dumps({'content': text})}\n\n"
                            except json.JSONDecodeError:
                                continue
                    logger.info(f"[TextService] Stream DashScope Response - Completed")
                    yield "data: [DONE]\n\n"
        except httpx.ConnectError as e:
            logger.error(f"[TextService] Stream DashScope Error - ConnectError: {e}")
            yield f"data: {json.dumps({'error': f'无法连接到 API 服务器: {url}，请检查网络或配置代理'})}\n\n"
        except httpx.TimeoutException as e:
            logger.error(f"[TextService] Stream DashScope Error - TimeoutException: {e}")
            yield f"data: {json.dumps({'error': '请求超时，请检查网络连接'})}\n\n"
