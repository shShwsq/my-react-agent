from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.auth import get_current_user
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import success

router = APIRouter(prefix="/api/user", tags=["user-preferences"])


class PreferenceRequest(BaseModel):
    key: str
    value: str


@router.post("/preferences")
def set_user_preference(
    request: PreferenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id,
        UserPreference.preference_key == request.key
    ).first()
    
    if pref:
        pref.preference_value = request.value
    else:
        pref = UserPreference(
            user_id=current_user.id,
            preference_key=request.key,
            preference_value=request.value
        )
        db.add(pref)
    
    db.commit()
    return success({"key": request.key, "value": request.value})


@router.get("/preferences")
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).all()
    
    return success({
        p.preference_key: p.preference_value
        for p in prefs
    })


@router.get("/preferences/{key}")
def get_user_preference(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id,
        UserPreference.preference_key == key
    ).first()
    
    if not pref:
        return success({"key": key, "value": None})
    
    return success({"key": key, "value": pref.preference_value})
