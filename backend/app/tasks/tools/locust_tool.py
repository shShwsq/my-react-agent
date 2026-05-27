import asyncio
import logging
import tempfile
import os
import json
import re
import subprocess as _subprocess
import sys as _sys
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from app.tasks.tools import BaseTool, ToolResult, tool_registry

logger = logging.getLogger(__name__)


@dataclass
class LocustRequest:
    """Locust请求配置"""
    name: str
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    body_type: str = "json"  # json, form, text
    # LLM 压测字段
    is_llm_request: bool = False
    llm_stream: bool = False
    llm_prompt: Optional[str] = None
    llm_model: Optional[str] = None
    # 自定义 LLM API 格式（非 OpenAI 标准格式时使用）
    llm_request_body: Optional[str] = None  # 自定义请求体 JSON 模板，用 {prompt} 占位
    llm_response_content_path: Optional[str] = None  # 响应中提取内容的路径，如 "choices.0.delta.content"


@dataclass
class LocustConfig:
    """Locust压测配置"""
    host: str
    users: int = 10
    spawn_rate: int = 1
    run_time: str = "60s"
    requests: List[LocustRequest] = field(default_factory=list)
    environment_vars: Optional[Dict[str, str]] = None
    # 环境变量到 header 的映射，如 {"API_KEY": "Authorization: Bearer {value}"}
    env_header_mapping: Optional[Dict[str, str]] = None


# OpenAI 格式压测的 Locust 模板
LLM_LOCUST_TEMPLATE = '''
import os
import time
import json
import re
from locust import HttpUser, task, between, events

class LLMUser(HttpUser):
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 动态从环境变量注入所有 header
        self.client.headers["Content-Type"] = "application/json"
{env_header_inject_code}

{task_methods}

# LLM 专属指标收集
_llm_stats = {{"ttft_samples": [], "tokens_per_sec_samples": [], "total_output_tokens": 0, "total_requests": 0}}


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception=None, **kwargs):
    if exception:
        return
    _llm_stats["total_requests"] += 1


@events.test_stop.add_listener
def on_test_stop(**kwargs):
    if _llm_stats["ttft_samples"]:
        avg_ttft = sum(_llm_stats["ttft_samples"]) / len(_llm_stats["ttft_samples"])
        print(f"\\n[LLM Metrics] Avg TTFT: {{avg_ttft:.1f}}ms")
        print(f"[LLM Metrics] TTFT samples: {{len(_llm_stats['ttft_samples'])}}")
    if _llm_stats["tokens_per_sec_samples"]:
        avg_tps = sum(_llm_stats["tokens_per_sec_samples"]) / len(_llm_stats["tokens_per_sec_samples"])
        print(f"[LLM Metrics] Avg Tokens/sec: {{avg_tps:.1f}}")
        print(f"[LLM Metrics] Tokens/sec samples: {{len(_llm_stats['tokens_per_sec_samples'])}}")
    print(f"[LLM Metrics] Total output tokens: {{_llm_stats['total_output_tokens']}}")
    print(f"[LLM Metrics] Total LLM requests: {{_llm_stats['total_requests']}}")
'''

# 普通 HTTP 压测的 Locust 模板
HTTP_LOCUST_TEMPLATE = '''
import os
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 动态从环境变量注入所有 header
{env_header_inject_code}

{task_methods}
'''


class LocustTool(BaseTool):
    name = "locust_tool"
    description = (
        "使用 Locust 对网站/API 进行性能压测。"
        "支持普通 HTTP 压测和 LLM/智能体 API 压测。"
        "LLM 压测支持 OpenAI 标准格式和自定义 API 格式，"
        "通过 llm_request_body 自定义请求体，通过 llm_response_content_path 指定响应解析路径。"
        "Streaming 模式可测量 TTFT（首 Token 延迟）和 tokens/sec 等指标。"
        "通过 environment_vars 安全传输敏感信息（如 API Key），"
        "通过 env_header_mapping 指定环境变量如何映射到请求头。"
        "默认以 Web UI 模式启动，用户可通过浏览器查看实时压测面板；"
        "设置 headless=true 时以无头模式运行，仅返回文本结果。"
    )

    def __init__(self):
        self._running_processes: dict = {}

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "目标网站的基础 URL（如 https://api.example.com）"
                },
                "users": {
                    "type": "integer",
                    "description": "并发用户数，默认 10",
                    "default": 10,
                    "minimum": 1
                },
                "spawn_rate": {
                    "type": "integer",
                    "description": "每秒启动的用户数，默认 1",
                    "default": 1,
                    "minimum": 1
                },
                "run_time": {
                    "type": "string",
                    "description": "压测运行时间，如 '60s', '5m', '1h'，默认 '60s'",
                    "default": "60s"
                },
                "requests": {
                    "type": "array",
                    "description": "要测试的请求列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "请求名称（用于报告显示）"
                            },
                            "method": {
                                "type": "string",
                                "description": "HTTP 方法：GET, POST, PUT, DELETE 等",
                                "default": "GET"
                            },
                            "url": {
                                "type": "string",
                                "description": "请求路径（相对于 host）"
                            },
                            "headers": {
                                "type": "object",
                                "description": "请求头，如 {'Content-Type': 'application/json'}"
                            },
                            "body": {
                                "type": "string",
                                "description": "请求体内容（JSON 字符串或表单数据）"
                            },
                            "body_type": {
                                "type": "string",
                                "description": "请求体类型：json, form, text",
                                "default": "json"
                            },
                            "is_llm_request": {
                                "type": "boolean",
                                "description": "是否为 LLM 请求。为 true 时启用 LLM 压测模式，可测量 TTFT 和 tokens/sec",
                                "default": False
                            },
                            "llm_stream": {
                                "type": "boolean",
                                "description": "LLM 请求是否使用 streaming 模式（仅 is_llm_request=true 时生效）",
                                "default": False
                            },
                            "llm_prompt": {
                                "type": "string",
                                "description": "LLM 请求的 prompt 内容（仅 is_llm_request=true 时生效，默认 'Hello'）",
                                "default": "Hello"
                            },
                            "llm_model": {
                                "type": "string",
                                "description": "LLM 模型名称（仅 is_llm_request=true 时生效，如 'gpt-3.5-turbo'）"
                            },
                            "llm_request_body": {
                                "type": "string",
                                "description": "自定义 LLM 请求体 JSON 模板（仅 is_llm_request=true 时生效）。使用 {prompt} 代表 prompt 内容，{model} 代表模型名。不设置时默认使用 OpenAI chat/completions 格式。示例：'{\"agent_id\": 215, \"messages\": [{\"role\": \"user\", \"content\": \"{prompt}\"}], \"agent_other\": {\"image_url\": \"\"}}'",
                                "default": None
                            },
                            "llm_response_content_path": {
                                "type": "string",
                                "description": "SSE 响应 JSON 中提取生成内容的路径（仅 is_llm_request=true 且 llm_stream=true 时生效）。点分路径格式，数字表示数组索引。不设置时默认使用 OpenAI 格式 'choices.0.delta.content'。示例：'data.content' 或 'result.answer'",
                                "default": None
                            }
                        },
                        "required": ["name", "url"]
                    }
                },
                "environment_vars": {
                    "type": "object",
                    "description": "环境变量（如 API_KEY），会安全地注入到 Locust 进程中，不会出现在日志中。值为空字符串的环境变量会在执行时弹窗让用户输入，因此不需要向用户询问敏感信息的值，只需将键名设为空字符串即可。键名会自动映射到请求头：API_KEY → Authorization: Bearer {value}，也可通过 env_header_mapping 自定义映射"
                },
                "env_header_mapping": {
                    "type": "object",
                    "description": "环境变量到请求头的映射规则。键为环境变量名，值为 header 格式字符串（{value} 代表变量值）。例如：{\"API_KEY\": \"Authorization: Bearer {value}\", \"X_TOKEN\": \"X-API-Key: {value}\"}。未指定的环境变量默认：API_KEY → Authorization: Bearer {value}",
                    "default": {}
                },
                "headless": {
                    "type": "boolean",
                    "description": "是否以无头模式运行。默认 false（Web UI 模式），用户可通过浏览器查看实时压测面板。设为 true 时仅返回文本结果",
                    "default": False
                },
                "web_ui_port": {
                    "type": "integer",
                    "description": "Locust Web UI 监听端口，默认 8089（仅 Web UI 模式生效）",
                    "default": 8089
                }
            },
            "required": ["host"]
        }

    def _build_env_header_inject_code(self, config: LocustConfig) -> str:
        """生成从环境变量动态注入 header 的代码"""
        lines = []
        env_vars = config.environment_vars or {}
        mapping = config.env_header_mapping or {}

        for var_name in env_vars:
            if var_name in mapping:
                # 用户自定义映射，格式如 "X-API-Key: {value}"
                header_format = mapping[var_name]
                # 解析 header 名和值模板
                if ": " in header_format:
                    header_name, header_value_template = header_format.split(": ", 1)
                    if "{value}" in header_value_template:
                        value_expr = header_value_template.replace("{value}", '" + env_val + "')
                        lines.append(
                            f'        env_val = os.environ.get("{var_name}", "")\n'
                            f'        if env_val:\n'
                            f'            self.client.headers["{header_name}"] = {repr(value_expr)}'
                        )
                    else:
                        lines.append(
                            f'        env_val = os.environ.get("{var_name}", "")\n'
                            f'        if env_val:\n'
                            f'            self.client.headers["{header_name}"] = "{header_value_template}"'
                        )
                else:
                    # 整个值就是 header 名
                    lines.append(
                        f'        env_val = os.environ.get("{var_name}", "")\n'
                        f'        if env_val:\n'
                        f'            self.client.headers["{header_format}"] = env_val'
                    )
            elif var_name == "API_KEY":
                # 默认：API_KEY → Authorization: Bearer
                lines.append(
                    '        env_val = os.environ.get("API_KEY", "")\n'
                    '        if env_val:\n'
                    '            self.client.headers["Authorization"] = f"Bearer {env_val}"'
                )
            else:
                # 其他环境变量：直接作为 header，变量名即 header 名
                lines.append(
                    f'        env_val = os.environ.get("{var_name}", "")\n'
                    f'        if env_val:\n'
                    f'            self.client.headers["{var_name}"] = env_val'
                )

        return "\n".join(lines)

    def _build_extract_content_code(self, content_path: str) -> str:
        """生成从 SSE chunk JSON 中按路径提取 content 的代码"""
        parts = content_path.split(".")
        code = "chunk"
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            if part.isdigit():
                code += f"[{part}]"
            else:
                # 判断下一个 part 是否为数字索引，如果是则默认值为 [] 否则为 {}
                next_is_index = (i + 1 < len(parts) and parts[i + 1].isdigit())
                default = "[]" if next_is_index else "{}"
                if is_last:
                    default = '""'
                code += f'.get("{part}", {default})'
        return code

    def _build_llm_task_method(self, req: LocustRequest) -> str:
        """生成 LLM 请求的 task 方法，支持 OpenAI 标准格式和自定义 API 格式"""
        func_name = req.name.replace(' ', '_')
        url = req.url
        prompt = (req.llm_prompt or "Hello").replace('"', '\\"')
        model = req.llm_model or ""
        stream = req.llm_stream

        # 构建请求体
        if req.llm_request_body:
            # 自定义请求体模板，安全地嵌入为 Python 字符串字面量（json.dumps 自动转义特殊字符）
            # 生成的 Python 代码在运行时通过 json.loads 反序列化，再替换 {prompt}/{model} 占位符
            safe_template = json.dumps(req.llm_request_body)
            payload_code = (
                f"payload_template = {safe_template}\n"
                "        payload_str = payload_template.replace('{prompt}', prompt).replace('{model}', model)\n"
                "        payload = json.loads(payload_str)"
            )
        else:
            # OpenAI 标准格式
            payload_code = f'payload = {{"model": model, "messages": [{{"role": "user", "content": prompt}}], "stream": {str(stream)}}}'

        # 构建响应内容提取代码
        if req.llm_response_content_path:
            extract_code = self._build_extract_content_code(req.llm_response_content_path)
        else:
            # OpenAI 默认路径
            extract_code = 'chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")'

        if stream:
            # streaming 模式：测量 TTFT 和 tokens/sec
            method_code = f'''
    @task
    def {func_name}(self):
        prompt = "{prompt}"
        model = "{model}"
        {payload_code}
        start_time = time.time()
        first_token_time = None
        token_count = 0
        try:
            with self.client.post("{url}", json=payload, stream=True, catch_response=True, name="{req.name}") as response:
                if response.status_code != 200:
                    response.failure(f"HTTP {{response.status_code}}")
                    return
                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.decode("utf-8", errors="replace")
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            content = {extract_code}
                            if content:
                                token_count += 1
                                if first_token_time is None:
                                    first_token_time = time.time()
                        except json.JSONDecodeError:
                            pass
                if first_token_time:
                    ttft = (first_token_time - start_time) * 1000
                    elapsed = time.time() - start_time
                    tps = token_count / elapsed if elapsed > 0 else 0
                    _llm_stats["ttft_samples"].append(ttft)
                    _llm_stats["tokens_per_sec_samples"].append(tps)
                    _llm_stats["total_output_tokens"] += token_count
                response.success()
        except Exception as e:
            pass
'''
        else:
            # 非流式模式：普通请求
            method_code = f'''
    @task
    def {func_name}(self):
        prompt = "{prompt}"
        model = "{model}"
        {payload_code}
        self.client.post("{url}", json=payload, name="{req.name}")
'''
        return method_code

    def _build_http_task_method(self, req: LocustRequest) -> str:
        """生成普通 HTTP 请求的 task 方法"""
        func_name = req.name.replace(' ', '_')

        headers_code = ""
        if req.headers:
            headers_code = f", headers={json.dumps(req.headers)}"

        body_code = ""
        if req.body:
            if req.body_type == "json":
                body_code = f", json={req.body}"
            elif req.body_type == "form":
                body_code = f", data={req.body}"
            else:
                body_code = f", data={json.dumps(req.body)}"

        return f'''
    @task
    def {func_name}(self):
        self.client.{req.method.lower()}("{req.url}"{headers_code}{body_code})
'''

    def _generate_locustfile(self, config: LocustConfig) -> str:
        """生成 Locust 测试文件内容"""
        has_llm = any(req.is_llm_request for req in config.requests)

        # 生成环境变量注入代码
        env_header_inject_code = self._build_env_header_inject_code(config)

        # 生成 task 方法
        task_methods = ""
        for req in config.requests:
            if req.is_llm_request:
                task_methods += self._build_llm_task_method(req)
            else:
                task_methods += self._build_http_task_method(req)

        # 选择模板
        if has_llm:
            template = LLM_LOCUST_TEMPLATE
        else:
            template = HTTP_LOCUST_TEMPLATE

        return template.format(
            env_header_inject_code=env_header_inject_code,
            task_methods=task_methods,
        )

    @staticmethod
    async def _run_subprocess(cmd: list, env: dict) -> _subprocess.Popen:
        """跨平台运行子进程（解决 Windows Python 3.14+ 兼容性问题）"""
        if _sys.platform == "win32":
            loop = asyncio.get_running_loop()
            popen = await loop.run_in_executor(None, lambda: _subprocess.Popen(
                cmd,
                stdout=_subprocess.PIPE,
                stderr=_subprocess.PIPE,
                env=env,
            ))
            return popen
        else:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            return proc

    @staticmethod
    def _clean_host(host: str) -> str:
        """清理 host URL：去除各种包围字符、首尾空格、尾部斜杠"""
        # 用 replace 逐字符清理，比正则更可靠（避免 raw string 中 \u 转义问题）
        for ch in ('\u0060', '\u2018', '\u2019', '\u201c', '\u201d', '\uff07', "'", '"'):
            host = host.replace(ch, '')
        return host.strip().rstrip('/')

    async def execute(self, host: str, users: int = 10, spawn_rate: int = 1,
                      run_time: str = "60s", requests: Optional[List[Dict[str, Any]]] = None,
                      environment_vars: Optional[Dict[str, str]] = None,
                      env_header_mapping: Optional[Dict[str, str]] = None,
                      headless: bool = False,
                      web_ui_port: int = 8089,
                      **kwargs) -> ToolResult:

        try:
            # 清理 host URL（去除 Brain Agent 可能添加的各种反引号）
            raw_host = host
            host = self._clean_host(host)
            if host != raw_host:
                logger.info(f"[LocustTool] Host 已清理: {raw_host!r} → {host!r}")

            logger.info(
                f"[LocustTool] 开始执行 | host={host} users={users} spawn_rate={spawn_rate} "
                f"run_time={run_time} headless={headless} requests_count={len(requests or [])} "
                f"env_vars_keys={list((environment_vars or {}).keys())} "
                f"env_mapping={env_header_mapping}"
            )

            # 验证请求配置
            if not requests or len(requests) == 0:
                return ToolResult(
                    success=False,
                    output=None,
                    error="请至少配置一个测试请求"
                )

            # 构建配置
            request_objects = []
            for req in requests:
                r = LocustRequest(
                    name=req.get("name", "unnamed"),
                    method=req.get("method", "GET"),
                    url=req.get("url", ""),
                    headers=req.get("headers"),
                    body=req.get("body"),
                    body_type=req.get("body_type", "json"),
                    is_llm_request=req.get("is_llm_request", False),
                    llm_stream=req.get("llm_stream", False),
                    llm_prompt=req.get("llm_prompt"),
                    llm_model=req.get("llm_model"),
                    llm_request_body=req.get("llm_request_body"),
                    llm_response_content_path=req.get("llm_response_content_path"),
                )
                request_objects.append(r)
                lrb_len = len(r.llm_request_body) if r.llm_request_body else 0
                logger.info(
                    f"[LocustTool] 请求 #{len(request_objects)}: name={r.name} method={r.method} url={r.url} "
                    f"is_llm={r.is_llm_request} stream={r.llm_stream} "
                    f"prompt_len={len(r.llm_prompt or '')} model={r.llm_model} "
                    f"llm_request_body_len={lrb_len} content_path={r.llm_response_content_path}"
                )

            config = LocustConfig(
                host=host,
                users=users,
                spawn_rate=spawn_rate,
                run_time=run_time,
                requests=request_objects,
                environment_vars=environment_vars,
                env_header_mapping=env_header_mapping,
            )

            # 生成 Locustfile
            locustfile_content = self._generate_locustfile(config)

            logger.info(f"[LocustTool] Locustfile 已生成, 大小: {len(locustfile_content)} 字符")
            logger.debug(f"[LocustTool] Locustfile 内容:\n{self._sanitize_output(locustfile_content, environment_vars)}")

            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(locustfile_content)
                temp_file = f.name

            logger.info(f"[LocustTool] 临时文件: {temp_file}")

            try:
                # 构建环境变量
                env = os.environ.copy()
                if environment_vars:
                    for key, value in environment_vars.items():
                        env[key] = value
                        logger.info(f"[LocustTool] 注入环境变量: {key}=***")

                # 构建命令
                cmd = [
                    "locust",
                    "-f", temp_file,
                    "--host", host,
                    "--users", str(users),
                    "--spawn-rate", str(spawn_rate),
                    "--run-time", run_time,
                ]

                if headless:
                    cmd.extend(["--headless", "--only-summary"])
                else:
                    cmd.extend(["--web-port", str(web_ui_port), "--bind-host", "0.0.0.0"])

                logger.info(f"[LocustTool] 启动命令: {' '.join(cmd)}")
                logger.info(f"[LocustTool] headless={headless} web_ui_port={web_ui_port}")

                # 启动 Locust 进程（跨平台兼容：Windows 上用线程包装 subprocess.Popen）
                process = await self._run_subprocess(cmd, env)

                logger.info(f"[LocustTool] 进程已启动, PID={process.pid}")

                _loop = asyncio.get_running_loop()

                if headless:
                    # 无头模式：等待进程完成
                    logger.info(f"[LocustTool] 等待进程完成 (headless mode)...")
                    stdout, stderr = await _loop.run_in_executor(None, process.communicate)
                    output = stdout.decode('utf-8', errors='replace') if isinstance(stdout, bytes) else (stdout or "")
                    error_output = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else (stderr or "")
                    combined_output = output + "\n" + error_output

                    logger.info(
                        f"[LocustTool] 进程已退出 | returncode={process.returncode} "
                        f"stdout_len={len(stdout) if stdout else 0} stderr_len={len(stderr) if stderr else 0}"
                    )

                    if process.returncode != 0:
                        sanitized_error = self._sanitize_output(error_output or output, environment_vars)
                        logger.error(f"[LocustTool] 压测失败 (returncode={process.returncode}): {sanitized_error}")
                        logger.error(f"[LocustTool] 原始 stderr: {error_output[:1000]}")
                        logger.error(f"[LocustTool] 原始 stdout: {output[:1000]}")
                        return ToolResult(
                            success=False,
                            output=output,
                            error=sanitized_error or f"进程返回非零退出码: {process.returncode}"
                        )

                    # 解析结果
                    has_llm = any(req.is_llm_request for req in request_objects)
                    result_data = self._parse_locust_output(combined_output, has_llm=has_llm)

                    return ToolResult(
                        success=True,
                        output={
                            "summary": self._sanitize_output(combined_output, environment_vars),
                            "parsed": result_data,
                            "config": {
                                "host": host,
                                "users": users,
                                "spawn_rate": spawn_rate,
                                "run_time": run_time,
                                "request_count": len(requests),
                                "has_llm_requests": has_llm,
                                "headless": True,
                            }
                        },
                        metadata={"return_code": process.returncode}
                    )
                else:
                    # Web UI 模式：等待进程启动，返回 Web UI 地址
                    await asyncio.sleep(2)

                    logger.info(
                        f"[LocustTool] Web UI 启动检查 | returncode={process.returncode} "
                        f"pid={process.pid} is_alive={process.returncode is None}"
                    )

                    # 检查进程是否仍在运行（启动失败会立即退出）
                    if process.returncode is not None:
                        stdout_data = await _loop.run_in_executor(None, process.stdout.read) if process.stdout else b""
                        stderr_data = await _loop.run_in_executor(None, process.stderr.read) if process.stderr else b""
                        error_output = stderr_data.decode('utf-8', errors='replace') if isinstance(stderr_data, bytes) else ""
                        stdout_output = stdout_data.decode('utf-8', errors='replace') if isinstance(stdout_data, bytes) else ""
                        sanitized_error = self._sanitize_output(error_output, environment_vars)
                        logger.error(
                            f"[LocustTool] Web UI 启动失败 | returncode={process.returncode} "
                            f"stderr_len={len(stderr_data)} stdout_len={len(stdout_data)}"
                        )
                        if error_output:
                            logger.error(f"[LocustTool] Web UI stderr: {error_output[:2000]}")
                        if stdout_output:
                            logger.error(f"[LocustTool] Web UI stdout: {stdout_output[:2000]}")
                        logger.error(f"[LocustTool] 完整启动命令: {' '.join(cmd)}")
                        return ToolResult(
                            success=False,
                            output=stdout_output,
                            error=sanitized_error or "Locust Web UI 启动失败"
                        )

                    # 注册进程以便后续停止
                    process_id = id(process)
                    self._running_processes[process_id] = process

                    web_ui_url = f"http://localhost:{web_ui_port}"
                    logger.info(f"[LocustTool] Web UI 已启动: {web_ui_url}, PID: {process.pid}")

                    has_llm = any(req.is_llm_request for req in request_objects)

                    return ToolResult(
                        success=True,
                        output={
                            "web_ui_url": web_ui_url,
                            "web_ui_port": web_ui_port,
                            "pid": process.pid,
                            "process_id": process_id,
                            "config": {
                                "host": host,
                                "users": users,
                                "spawn_rate": spawn_rate,
                                "run_time": run_time,
                                "request_count": len(requests),
                                "has_llm_requests": has_llm,
                                "headless": False,
                            }
                        },
                        metadata={"mode": "web_ui", "pid": process.pid}
                    )

            finally:
                # Web UI 模式下不删除临时文件（进程还在用）
                if headless and os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"[LocustTool] 清理临时文件: {temp_file}")

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"[LocustTool] 未捕获异常: {type(e).__name__}: {e}")
            logger.error(f"[LocustTool] Traceback:\n{tb}")
            return ToolResult(
                success=False,
                output=None,
                error=f"{type(e).__name__}: {e}" if str(e) else f"未捕获异常: {type(e).__name__}"
            )

    async def stop_process(self, process_id: int) -> bool:
        """停止指定的 Locust Web UI 进程"""
        process = self._running_processes.get(process_id)
        if not process:
            return False
        try:
            process.terminate()
            loop = asyncio.get_running_loop()
            await asyncio.wait_for(loop.run_in_executor(None, process.wait), timeout=5)
        except asyncio.TimeoutError:
            process.kill()
        except Exception as e:
            logger.warning(f"[LocustTool] 停止进程异常: {e}")
        finally:
            self._running_processes.pop(process_id, None)
        logger.info(f"[LocustTool] 已停止 Locust 进程: {process_id}")
        return True

    async def stop_all_processes(self):
        """停止所有运行中的 Locust 进程"""
        pids = list(self._running_processes.keys())
        for pid in pids:
            await self.stop_process(pid)

    def _sanitize_output(self, output: str, sensitive_vars: Optional[Dict[str, str]]) -> str:
        """清理输出中的敏感信息"""
        if not sensitive_vars:
            return output

        sanitized = output
        for value in sensitive_vars.values():
            if value and len(value) > 4:
                sanitized = sanitized.replace(value, value[:4] + "***")
        return sanitized

    def _parse_locust_output(self, output: str, has_llm: bool = False) -> Dict[str, Any]:
        """解析 Locust 输出，提取关键指标，支持 LLM 专属指标"""
        result = {
            "total_requests": 0,
            "total_failures": 0,
            "requests_per_second": 0.0,
            "avg_response_time": 0.0,
            "min_response_time": 0.0,
            "max_response_time": 0.0,
            "p50_response_time": 0.0,
            "p95_response_time": 0.0,
            "p99_response_time": 0.0,
        }

        if has_llm:
            result["llm_metrics"] = {
                "avg_ttft_ms": 0.0,
                "avg_tokens_per_sec": 0.0,
                "total_output_tokens": 0,
                "ttft_samples": 0,
                "tps_samples": 0,
            }

        lines = output.strip().split('\n')
        for line in lines:
            line = line.strip()

            # LLM 专属指标
            if has_llm:
                m = re.search(r'Avg TTFT:\s*([\d.]+)\s*ms', line)
                if m:
                    result["llm_metrics"]["avg_ttft_ms"] = float(m.group(1))
                    continue
                m = re.search(r'TTFT samples:\s*(\d+)', line)
                if m:
                    result["llm_metrics"]["ttft_samples"] = int(m.group(1))
                    continue
                m = re.search(r'Avg Tokens/sec:\s*([\d.]+)', line)
                if m:
                    result["llm_metrics"]["avg_tokens_per_sec"] = float(m.group(1))
                    continue
                m = re.search(r'Tokens/sec samples:\s*(\d+)', line)
                if m:
                    result["llm_metrics"]["tps_samples"] = int(m.group(1))
                    continue
                m = re.search(r'Total output tokens:\s*(\d+)', line)
                if m:
                    result["llm_metrics"]["total_output_tokens"] = int(m.group(1))
                    continue

            # 通用指标 - 使用正则更可靠地解析
            m = re.search(r'Total requests\s+(\d+)', line)
            if m:
                result["total_requests"] = int(m.group(1))
                continue
            m = re.search(r'Total failures\s+(\d+)', line)
            if m:
                result["total_failures"] = int(m.group(1))
                continue

            # 解析 Locust 表格行（Aggregated 格式）
            # 格式: Type     Name                                                     # reqs      # fails |    Avg     Min     Max  Median |   req/s  failures/s
            # 或: GET      /api/users                                                 123     0(0.00%) |    150      50     800     120 |   12.30       0.00
            m = re.match(
                r'(GET|POST|PUT|DELETE|PATCH|HEAD)\s+\S+\s+(\d+)\s+[\d(.,%)+]+\s*\|\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\|\s*([\d.]+)',
                line
            )
            if m:
                result["total_requests"] = int(m.group(2))
                result["avg_response_time"] = float(m.group(3))
                result["min_response_time"] = float(m.group(4))
                result["max_response_time"] = float(m.group(5))
                result["p50_response_time"] = float(m.group(6))
                result["requests_per_second"] = float(m.group(7))
                continue

            # Aggregated 行
            m = re.match(
                r'Aggregated\s+(\d+)\s+[\d(.,%)+]+\s*\|\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\|\s*([\d.]+)',
                line
            )
            if m:
                result["total_requests"] = int(m.group(1))
                result["avg_response_time"] = float(m.group(2))
                result["min_response_time"] = float(m.group(3))
                result["max_response_time"] = float(m.group(4))
                result["p50_response_time"] = float(m.group(5))
                result["requests_per_second"] = float(m.group(6))
                continue

            # Response time percentile 行
            m = re.search(r'50%\s+([\d.]+)', line)
            if m:
                result["p50_response_time"] = float(m.group(1))
                continue
            m = re.search(r'95%\s+([\d.]+)', line)
            if m:
                result["p95_response_time"] = float(m.group(1))
                continue
            m = re.search(r'99%\s+([\d.]+)', line)
            if m:
                result["p99_response_time"] = float(m.group(1))
                continue

            # 旧格式兼容
            if "Requests/sec" in line:
                try:
                    result["requests_per_second"] = float(line.split()[-1])
                except (ValueError, IndexError):
                    pass

        return result


locust_tool = LocustTool()
tool_registry.register(locust_tool)
