from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, ProfileUpdate, success, fail, ErrorCode

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise fail(ErrorCode.USER_EXISTS)
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(data={"sub": user.username})
    return success({"access_token": access_token, "token_type": "bearer"}, "注册成功")


@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise fail(ErrorCode.AUTH_FAILED)
    access_token = create_access_token(data={"sub": user.username})
    return success({"access_token": access_token, "token_type": "bearer"}, "登录成功")


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success({
        "id": current_user.id,
        "username": current_user.username,
        "is_super": current_user.is_super,
    })


@router.put("/profile")
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(profile_data.current_password, current_user.hashed_password):
        raise fail(ErrorCode.AUTH_FAILED)

    if profile_data.username != current_user.username:
        existing = db.query(User).filter(User.username == profile_data.username).first()
        if existing:
            raise fail(ErrorCode.USER_EXISTS)
        current_user.username = profile_data.username

    if profile_data.new_password:
        current_user.hashed_password = get_password_hash(profile_data.new_password)

    db.commit()
    db.refresh(current_user)

    access_token = create_access_token(data={"sub": current_user.username})
    return success({
        "access_token": access_token,
        "token_type": "bearer",
        "username": current_user.username
    }, "修改成功")
