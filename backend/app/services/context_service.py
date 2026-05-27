import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models import UserPreference, Message, RoomVariable

logger = logging.getLogger(__name__)


class ContextService:
    def __init__(self, db: Session):
        self.db = db
    
    async def build_context(
        self,
        user_id: int,
        room_id: str,
        current_input: str,
        base_context: Optional[dict] = None
    ) -> dict:
        full_context = base_context.copy() if base_context else {}
        
        user_prefs = self._load_user_preferences(user_id)
        conversation_history = self._load_conversation_history(room_id)
        active_variables = self._load_active_variables(room_id)
        
        full_context.update({
            "user_input": current_input,
            "conversation_history": conversation_history,
            "active_variables": active_variables,
            "user_preferences": user_prefs,
            "room_id": room_id,
            "user_id": user_id
        })
        
        logger.info(f"[ContextService] Built context - history: {len(conversation_history)} messages, variables: {len(active_variables)}, prefs: {len(user_prefs)}")
        
        return full_context
    
    def _load_user_preferences(self, user_id: int) -> dict:
        prefs = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()
        return {p.preference_key: p.preference_value for p in prefs}
    
    def _load_conversation_history(self, room_id: str, limit: int = 20) -> list:
        messages = self.db.query(Message).filter(
            Message.room_id == room_id
        ).order_by(Message.id.desc()).limit(limit).all()
        
        history = []
        for msg in reversed(messages):
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history
    
    def _load_active_variables(self, room_id: str) -> list:
        variables = self.db.query(RoomVariable).filter(
            RoomVariable.room_id == room_id
        ).all()
        return [v.variable_name for v in variables]
    
    def set_user_preference(self, user_id: int, key: str, value: str):
        pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_key == key
        ).first()
        
        if pref:
            pref.preference_value = value
        else:
            pref = UserPreference(
                user_id=user_id,
                preference_key=key,
                preference_value=value
            )
            self.db.add(pref)
        
        self.db.commit()
        logger.info(f"[ContextService] Set user preference: {key}={value}")
    
    def get_user_preference(self, user_id: int, key: str) -> Optional[str]:
        pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_key == key
        ).first()
        return pref.preference_value if pref else None
