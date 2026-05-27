import json
import logging
import base64
import uuid
from pathlib import Path
from typing import Optional, AsyncGenerator
from app.services.vision_service import VisionService
from app.services.variable_service import VariableService
from app.tasks.image_operations.registry import (
    BaseImageOperation,
    image_operation_registry
)
from app.schemas import ApiResponse

logger = logging.getLogger(__name__)

FILES_DIR = Path("storage/agent_files")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}


def img_success(data: dict) -> str:
    return ApiResponse(e="", m="", d=data).model_dump_json()


def img_error(error_code: str, message: str) -> str:
    return ApiResponse(e=error_code, m=message, d=None).model_dump_json()


class ImageUnderstandOperation(BaseImageOperation):
    name = "image_understand"
    description = "理解图片内容并提取文字（流式输出）。支持读取上传的图片文件，使用视觉模型理解图片内容。"
    
    def __init__(self, vision_service: Optional[VisionService] = None):
        self.vision_service = vision_service or VisionService()
    
    async def execute(self, **kwargs) -> AsyncGenerator[str, None]:
        filename = kwargs.get("filename", "")
        prompt = kwargs.get("prompt", "请提取图片中的所有文字内容，如果图片中没有文字，请描述图片内容")
        output_variable = kwargs.get("output_variable", "")
        
        api_key = kwargs.get("vision_api_key", "")
        api_url = kwargs.get("vision_api_url", "")
        model = kwargs.get("vision_model", "")
        call_method = kwargs.get("vision_call_method", "")
        
        variable_service: Optional[VariableService] = kwargs.get("variable_service")
        room_id = kwargs.get("room_id", "")
        user_id = kwargs.get("user_id", 0)
        folder = kwargs.get("folder", "uploads")
        
        if not filename:
            yield img_error("IMAGE_OP_ERROR", "缺少 filename 参数")
            return
        
        if not api_key or not model:
            yield img_error("IMAGE_OP_ERROR", "用户未配置图片理解模型")
            return
        
        file_path = FILES_DIR / str(user_id) / room_id / folder / filename
        if not file_path.exists():
            yield img_error("IMAGE_OP_ERROR", f"图片文件不存在: {filename}")
            return
        
        ext = file_path.suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            yield img_error("IMAGE_OP_ERROR", f"不支持的图片格式: {ext}")
            return
        
        try:
            with open(file_path, "rb") as f:
                image_data = f.read()
            
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".bmp": "image/bmp",
                ".webp": "image/webp",
                ".svg": "image/svg+xml",
            }
            mime_type = mime_types.get(ext, "image/png")
            image_url = f"data:{mime_type};base64,{image_base64}"
            
            logger.info(f"[ImageUnderstand] Processing image: {filename}, size: {len(image_data)} bytes")
            
        except Exception as e:
            logger.error(f"[ImageUnderstand] Failed to read image: {e}")
            yield img_error("IMAGE_OP_ERROR", f"读取图片失败: {str(e)}")
            return
        
        full_content = ""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            async for chunk in self.vision_service.stream_image_understanding(
                messages=messages,
                model=model,
                api_key=api_key,
                url=api_url,
                call_method=call_method,
                image_url=image_url
            ):
                if chunk.startswith("data: "):
                    data_str = chunk[6:].strip()
                    if data_str and data_str != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            if "content" in data:
                                content_piece = data["content"]
                                full_content += content_piece
                                yield img_success({"type": "content", "content": content_piece})
                        except json.JSONDecodeError:
                            pass
            
            if not full_content:
                yield img_error("IMAGE_OP_ERROR", "视觉模型未生成任何内容")
                return
            
            logger.info(f"[ImageUnderstand] Extracted content length: {len(full_content)}")
            
            if output_variable and variable_service:
                success = variable_service.set_variable(room_id, output_variable, full_content)
                if success:
                    logger.info(f"[ImageUnderstand] Content stored in variable: {output_variable}")
                    yield img_success({
                        "type": "complete",
                        "variable_name": output_variable,
                        "content_length": len(full_content),
                        "variable_value": full_content
                    })
                else:
                    yield img_error("IMAGE_OP_ERROR", f"无法存储变量: {output_variable}")
                    return
            else:
                yield img_success({
                    "type": "complete",
                    "content": full_content,
                    "content_length": len(full_content)
                })
            
        except Exception as e:
            logger.error(f"[ImageUnderstand] Error: {e}")
            yield img_error("IMAGE_OP_ERROR", str(e))
    
    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "图片文件名（需已上传到 uploads 文件夹）"
                },
                "prompt": {
                    "type": "string",
                    "description": "对图片的理解提示，如'提取图片中的文字'或'描述图片内容'。默认提取文字"
                },
                "output_variable": {
                    "type": "string",
                    "description": "存储提取内容的变量名（可选），后续可通过 {{变量名}} 引用"
                },
                "folder": {
                    "type": "string",
                    "enum": ["uploads", "outputs"],
                    "description": "图片所在文件夹，默认 uploads"
                }
            },
            "required": ["filename"]
        }


image_operation_registry.register(ImageUnderstandOperation())


class ImageGenerateOperation(BaseImageOperation):
    name = "image_generate"
    description = "生成图片并保存到文件。使用图片生成模型根据文本描述生成图片。"
    
    def __init__(self, vision_service: Optional[VisionService] = None):
        self.vision_service = vision_service or VisionService()
    
    async def execute(self, **kwargs) -> AsyncGenerator[str, None]:
        prompt = kwargs.get("prompt", "")
        size = kwargs.get("size", "1024*1024")
        n = kwargs.get("n", 1)
        negative_prompt = kwargs.get("negative_prompt")
        seed = kwargs.get("seed")
        
        api_key = kwargs.get("image_gen_api_key", "")
        api_url = kwargs.get("image_gen_api_url", "")
        model = kwargs.get("image_gen_model", "")
        call_method = kwargs.get("image_gen_call_method", "")
        
        room_id = kwargs.get("room_id", "")
        user_id = kwargs.get("user_id", 0)
        
        if not prompt:
            yield img_error("IMAGE_OP_ERROR", "缺少 prompt 参数")
            return
        
        if not api_key or not model:
            yield img_error("IMAGE_OP_ERROR", "用户未配置图片生成模型")
            return
        
        try:
            gen_kwargs = {}
            if negative_prompt:
                gen_kwargs["negative_prompt"] = negative_prompt
            if seed is not None:
                gen_kwargs["seed"] = seed
            
            logger.info(f"[ImageGenerate] Generating image with prompt: {prompt[:100]}, size: {size}, n: {n}")
            
            result = await self.vision_service.image_generation(
                prompt=prompt,
                model=model,
                call_method=call_method,
                api_key=api_key,
                url=api_url,
                size=size,
                n=n,
                **gen_kwargs
            )
            
            images = result.get("images", [])
            if not images:
                yield img_error("IMAGE_OP_ERROR", "图片生成失败：未返回图片")
                return
            
            outputs_dir = FILES_DIR / str(user_id) / room_id / "outputs"
            outputs_dir.mkdir(parents=True, exist_ok=True)
            
            saved_images = []
            for i, image_data in enumerate(images):
                try:
                    if image_data.startswith("http://") or image_data.startswith("https://"):
                        import httpx
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.get(image_data)
                            if response.status_code == 200:
                                image_bytes = response.content
                            else:
                                logger.error(f"[ImageGenerate] Failed to download image: {response.status_code}")
                                continue
                    elif image_data.startswith("data:"):
                        header, data = image_data.split(",", 1)
                        image_bytes = base64.b64decode(data)
                    else:
                        image_bytes = base64.b64decode(image_data)
                    
                    image_id = str(uuid.uuid4())[:8]
                    filename = f"generated_{image_id}_{i}.png"
                    file_path = outputs_dir / filename
                    
                    with open(file_path, "wb") as f:
                        f.write(image_bytes)
                    
                    saved_images.append({
                        "filename": filename,
                        "file_path": str(file_path),
                        "relative_path": file_path.relative_to(FILES_DIR).as_posix(),
                        "file_size": len(image_bytes)
                    })
                    
                    logger.info(f"[ImageGenerate] Saved image: {filename}, size: {len(image_bytes)} bytes")
                    
                except Exception as e:
                    logger.error(f"[ImageGenerate] Failed to save image {i}: {e}")
                    continue
            
            if not saved_images:
                yield img_error("IMAGE_OP_ERROR", "图片保存失败")
                return
            
            yield img_success({
                "type": "complete",
                "prompt": prompt,
                "images": saved_images,
                "count": len(saved_images),
                "message": f"成功生成 {len(saved_images)} 张图片"
            })
            
        except ValueError as e:
            logger.error(f"[ImageGenerate] API error: {e}")
            yield img_error("IMAGE_OP_ERROR", str(e))
        except Exception as e:
            logger.error(f"[ImageGenerate] Error: {e}")
            yield img_error("IMAGE_OP_ERROR", f"图片生成失败: {str(e)}")
    
    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "图片生成提示词，描述想要生成的图片内容"
                },
                "size": {
                    "type": "string",
                    "description": "图片尺寸，如 '512*512'、'1024*1024'、'720*1280' 等。默认 1024*1024"
                },
                "n": {
                    "type": "integer",
                    "description": "生成图片数量，默认 1"
                },
                "negative_prompt": {
                    "type": "string",
                    "description": "反向提示词，描述不想在图片中出现的内容（可选）"
                },
                "seed": {
                    "type": "integer",
                    "description": "随机种子，用于复现结果（可选）"
                }
            },
            "required": ["prompt"]
        }


image_operation_registry.register(ImageGenerateOperation())


class ImageToBase64Operation(BaseImageOperation):
    name = "image_to_base64"
    description = "将图片文件转换为 Base64 编码字符串，可存储到变量中供后续使用（如作为 LLM 请求的图片参数）。"
    
    async def execute(self, **kwargs) -> AsyncGenerator[str, None]:
        filename = kwargs.get("filename", "")
        output_variable = kwargs.get("output_variable", "")
        
        variable_service: Optional[VariableService] = kwargs.get("variable_service")
        room_id = kwargs.get("room_id", "")
        user_id = kwargs.get("user_id", 0)
        folder = kwargs.get("folder", "uploads")
        
        if not filename:
            yield img_error("IMAGE_OP_ERROR", "缺少 filename 参数")
            return
        
        file_path = FILES_DIR / str(user_id) / room_id / folder / filename
        if not file_path.exists():
            yield img_error("IMAGE_OP_ERROR", f"图片文件不存在: {filename}")
            return
        
        ext = file_path.suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            yield img_error("IMAGE_OP_ERROR", f"不支持的图片格式: {ext}")
            return
        
        try:
            with open(file_path, "rb") as f:
                image_data = f.read()
            
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".bmp": "image/bmp",
                ".webp": "image/webp",
                ".svg": "image/svg+xml",
            }
            mime_type = mime_types.get(ext, "image/png")
            data_uri = f"data:{mime_type};base64,{image_base64}"
            
            logger.info(f"[ImageToBase64] Converted: {filename}, size: {len(image_data)} bytes, base64 length: {len(image_base64)}")
            
            result_data = {
                "type": "complete",
                "filename": filename,
                "mime_type": mime_type,
                "file_size": len(image_data),
                "base64_length": len(image_base64),
            }
            
            if output_variable and variable_service:
                success = variable_service.set_variable(room_id, output_variable, data_uri)
                if success:
                    logger.info(f"[ImageToBase64] Stored in variable: {output_variable}")
                    result_data["variable_name"] = output_variable
                    result_data["message"] = f"Base64 已存储到变量 `{output_variable}`，可在参数中通过 {{{{{output_variable}}}}} 引用"
                    yield img_success(result_data)
                else:
                    yield img_error("IMAGE_OP_ERROR", f"无法存储变量: {output_variable}")
            else:
                # 没有指定变量名时自动生成一个
                auto_var = f"base64_{filename.replace('.', '_')}"
                if variable_service:
                    success = variable_service.set_variable(room_id, auto_var, data_uri)
                    if success:
                        result_data["variable_name"] = auto_var
                        result_data["message"] = f"Base64 已存储到变量 {{{{{auto_var}}}}}，可在参数中通过 {{{{{auto_var}}}}} 引用"
                        yield img_success(result_data)
                        return
                yield img_error("IMAGE_OP_ERROR", "必须指定 output_variable 或确保变量服务可用")
            
        except Exception as e:
            logger.error(f"[ImageToBase64] Error: {e}")
            yield img_error("IMAGE_OP_ERROR", f"图片转 Base64 失败: {str(e)}")
    
    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "图片文件名（需已上传到 uploads 或 outputs 文件夹）"
                },
                "output_variable": {
                    "type": "string",
                    "description": "存储 Base64 结果的变量名（可选），存储格式为 data URI（data:image/png;base64,...），后续可通过 {{变量名}} 引用"
                },
                "folder": {
                    "type": "string",
                    "enum": ["uploads", "outputs"],
                    "description": "图片所在文件夹，默认 uploads"
                }
            },
            "required": ["filename"]
        }


image_operation_registry.register(ImageToBase64Operation())
