from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Room, Message
from app.schemas import RoomCreate, MessageCreate, success, fail, ErrorCode
from app.services.variable_service import VariableService

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

def format_datetime(dt: datetime) -> str:
    utc_dt = dt.replace(tzinfo=timezone.utc)
    return utc_dt.isoformat()


@router.post("")
def create_room(
    data: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = Room(
        id=data.id,
        user_id=current_user.id,
        title=data.title or data.id,
        models=data.models
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return success({
        "id": room.id,
        "title": room.title,
        "models": room.models,
        "created_at": format_datetime(room.created_at),
        "messages": [],
    })


@router.get("")
def list_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rooms = (
        db.query(Room)
        .filter(Room.user_id == current_user.id)
        .order_by(Room.updated_at.desc())
        .all()
    )
    return success([{
        "id": r.id,
        "title": r.title,
        "created_at": format_datetime(r.created_at),
    } for r in rooms])


@router.get("/{room_id}")
def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id, Room.user_id == current_user.id).first()
    if not room:
        raise fail(ErrorCode.NOT_FOUND, "房间不存在")
    return success({
        "id": room.id,
        "title": room.title,
        "models": room.models,
        "created_at": format_datetime(room.created_at),
        "messages": [{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": format_datetime(m.created_at),
        } for m in room.messages],
    })


@router.post("/{room_id}/messages")
def add_message(
    room_id: str,
    msg: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id, Room.user_id == current_user.id).first()
    if not room:
        raise fail(ErrorCode.NOT_FOUND, "房间不存在")
    message = Message(room_id=room_id, role=msg.role, content=msg.content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return success({
        "id": message.id,
        "role": message.role,
        "content": message.content,
    })


@router.delete("/{room_id}")
def delete_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id, Room.user_id == current_user.id).first()
    if not room:
        raise fail(ErrorCode.NOT_FOUND, "房间不存在")
    db.delete(room)
    db.commit()
    return success(message="房间删除成功")


@router.get("/{room_id}/variables")
def get_room_variables(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id, Room.user_id == current_user.id).first()
    if not room:
        raise fail(ErrorCode.NOT_FOUND, "房间不存在")
    
    variable_service = VariableService(db)
    variables = variable_service.get_all_variables(room_id)
    
    return success({
        "variables": variables
    })
