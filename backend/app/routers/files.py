import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, AgentFile
from app.tasks.file_operations import list_files, get_file_path

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("storage/agent_files")

ALLOWED_EXTENSIONS = {
    # 文本文件
    ".txt", ".md", ".json", ".csv", ".html", ".htm", ".xml", ".yaml", ".yml",
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go",
    ".rs", ".rb", ".php", ".sh", ".bat", ".ps1", ".sql", ".r", ".m",
    ".ini", ".cfg", ".conf", ".log", ".toml", ".env",
    # 文档
    ".docx", ".pdf", ".pptx", ".xlsx",
    # 图片
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/list/{room_id}")
async def get_room_files(
    room_id: str,
    folder: str = Query("all", description="文件夹: all, outputs, uploads"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        files = list_files(room_id, current_user.id, folder)
        
        db_files = db.query(AgentFile).filter(
            AgentFile.room_id == room_id,
            AgentFile.user_id == current_user.id
        ).all()
        
        db_files_map = {f.filename: f for f in db_files}
        
        result = []
        for file_info in files:
            db_file = db_files_map.get(file_info["filename"])
            result.append({
                "filename": file_info["filename"],
                "folder": file_info.get("folder", ""),
                "file_size": file_info["file_size"],
                "relative_path": file_info["relative_path"],
                "created_at": file_info["created_at"],
                "id": db_file.id if db_file else None
            })
        
        return {"e": "", "d": {"files": result}, "m": ""}
        
    except Exception as e:
        logger.error(f"[FilesAPI] List error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{room_id}/{filename}")
async def download_file(
    room_id: str,
    filename: str,
    folder: str = Query("outputs", description="文件夹: outputs, uploads"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        file_path = get_file_path(filename, room_id, current_user.id, folder)
        
        if not file_path:
            for search_folder in ["outputs", "uploads"]:
                file_path = get_file_path(filename, room_id, current_user.id, search_folder)
                if file_path:
                    break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        db_file = db.query(AgentFile).filter(
            AgentFile.room_id == room_id,
            AgentFile.user_id == current_user.id,
            AgentFile.filename == filename
        ).first()
        
        if not db_file:
            db_file = AgentFile(
                room_id=room_id,
                user_id=current_user.id,
                filename=filename,
                file_path=str(file_path),
                file_size=file_path.stat().st_size
            )
            db.add(db_file)
            db.commit()
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FilesAPI] Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_file_record(
    room_id: str,
    filename: str,
    file_path: str,
    file_size: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        existing = db.query(AgentFile).filter(
            AgentFile.room_id == room_id,
            AgentFile.user_id == current_user.id,
            AgentFile.filename == filename
        ).first()
        
        if existing:
            existing.file_path = file_path
            existing.file_size = file_size
        else:
            db_file = AgentFile(
                room_id=room_id,
                user_id=current_user.id,
                filename=filename,
                file_path=file_path,
                file_size=file_size
            )
            db.add(db_file)
        
        db.commit()
        
        return {"success": True, "message": "文件记录已保存"}
        
    except Exception as e:
        logger.error(f"[FilesAPI] Save error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/{room_id}")
async def upload_file(
    room_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件到 agent_files/<user_id>/<room_id>/uploads/"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {ext}，允许的类型: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
        
        upload_dir = UPLOADS_DIR / str(current_user.id) / room_id / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 避免文件名冲突
        target_path = upload_dir / file.filename
        if target_path.exists():
            stem = Path(file.filename).stem
            counter = 1
            while target_path.exists():
                target_path = upload_dir / f"{stem}_{counter}{ext}"
                counter += 1
        
        with open(target_path, "wb") as f:
            f.write(content)
        
        # 保存数据库记录
        relative_path = f"{current_user.id}/{room_id}/uploads/{target_path.name}"
        existing = db.query(AgentFile).filter(
            AgentFile.room_id == room_id,
            AgentFile.user_id == current_user.id,
            AgentFile.filename == target_path.name
        ).first()
        
        if existing:
            existing.file_path = str(target_path)
            existing.file_size = len(content)
        else:
            db_file = AgentFile(
                room_id=room_id,
                user_id=current_user.id,
                filename=target_path.name,
                file_path=str(target_path),
                file_size=len(content)
            )
            db.add(db_file)
        
        db.commit()
        
        logger.info(f"[FilesAPI] Uploaded: {target_path.name} ({len(content)} bytes)")
        
        return {
            "e": "",
            "d": {
                "filename": target_path.name,
                "file_size": len(content),
                "relative_path": relative_path,
                "folder": "uploads"
            },
            "m": "上传成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FilesAPI] Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
