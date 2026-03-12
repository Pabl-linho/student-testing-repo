# app/domains/chat/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List, Sequence

from app.domains.chat import models, schemas

class ChatService: 
    # Service layer fih kamel logic te3 chat
    
    @staticmethod
    async def get_chat_members_ids(db: AsyncSession, chat_id: int) -> List[int]:
        """
        تجلب IDs تاع كامل الأعضاء اللي في شات معين (باش نبعثولهم رسائل في WebSocket)
        """
        query = select(models.ChatMember.user_id).where(models.ChatMember.chat_id == chat_id)
        result = await db.execute(query)
        # .scalars().all() ترجعلنا list تاع integers مباشرة [1, 2, 3]
        return list(result.scalars().all())

    @staticmethod
    async def verify_user_in_chat(db: AsyncSession, chat_id: int, user_id: int) -> bool:   
        """
        Security Check (IDOR/BOLA Protection - OWASP):
        نتأكدو بلي اليوزر راهو فعلا عضو في هاد الشات باش ما يقرعجش على شات خاطيه.
        """
        query = select(models.ChatMember).where(
            and_(
                models.ChatMember.chat_id == chat_id,
                models.ChatMember.user_id == user_id
            )
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this chat"
            )
        return True

    @staticmethod
    async def create_message(
        db: AsyncSession, 
        chat_id: int, 
        sender_id: int, 
        message_data: schemas.MessageCreate
    ) -> models.Message:
        
        # Security Check (نتأكدو بلي راهو عضو قبل ما يبعث الرسالة)
        await ChatService.verify_user_in_chat(db, chat_id, sender_id)
    
        new_message = models.Message( # Create a message (Database Logic)
            chat_id=chat_id,
            sender_id=sender_id,
            content=message_data.content,
            message_type=message_data.message_type
        )
        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)
        
        return new_message

    @staticmethod
    async def get_chat_history(
        db: AsyncSession, 
        chat_id: int, 
        user_id: int,
        limit: int = 40, 
        offset: int = 0
    ) -> Sequence[models.Message]:
       
        # Security Check (ما يقدرش يقرأ تاريخ شات خاطيه)
        await ChatService.verify_user_in_chat(db, chat_id, user_id)
        
        # نجبدوا الرسائل، ونديرو Pagination باستعمال limit و offset
        # .desc() باش نجيبو أحدث الرسائل أولا
        query = (
            select(models.Message)
            .where(models.Message.chat_id == chat_id)
            .where(models.Message.is_deleted == False)
            .order_by(models.Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        return result.scalars().all()

# Instance وحدة باش نقدرو نستعملوها في الـ Routers
chat_service = ChatService()