# app/domains/chat/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List, Sequence

from app.domains.chat import models, schemas

class ChatService: 
    # Service layer fih kamel logic te3 chat

    @staticmethod
    async def commit_and_refresh(db: AsyncSession, instance: models.Message) -> models.Message:
        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )

        await db.refresh(instance)
        return instance
    
    @staticmethod
    async def get_chat_members_ids(db: AsyncSession, chat_id: int) -> List[int]:
        """
        تجلب IDs تاع كامل الأعضاء اللي في شات معين (باش نبعثولهم رسائل في WebSocket)
        """
        query = (
            select(models.ChatMember.user_id)
            .where(models.ChatMember.chat_id == chat_id)
            .distinct()
        )
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
        return await ChatService.commit_and_refresh(db, new_message)

    @staticmethod
    async def get_owned_message(
        db: AsyncSession,
        chat_id: int,
        message_id: int,
        user_id: int,
        action: str
    ) -> models.Message:
        await ChatService.verify_user_in_chat(db, chat_id, user_id)

        query = select(models.Message).where(
            and_(
                models.Message.id == message_id,
                models.Message.chat_id == chat_id
            )
        )
        result = await db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        if message.sender_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You can only {action} your own messages"
            )

        return message

    @staticmethod
    async def update_message(
        db: AsyncSession,
        chat_id: int,
        message_id: int,
        user_id: int,
        message_data: schemas.MessageUpdate
    ) -> models.Message:
        message = await ChatService.get_owned_message(
            db,
            chat_id,
            message_id,
            user_id,
            "edit"
        )

        if message.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deleted messages cannot be edited"
            )

        message.content = message_data.content
        message.is_edited = True

        return await ChatService.commit_and_refresh(db, message)

    @staticmethod
    async def delete_message(
        db: AsyncSession,
        chat_id: int,
        message_id: int,
        user_id: int
    ) -> models.Message:
        message = await ChatService.get_owned_message(
            db,
            chat_id,
            message_id,
            user_id,
            "delete"
        )

        if message.is_deleted:
            return message

        message.is_deleted = True
        message.content = ""

        return await ChatService.commit_and_refresh(db, message)

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
            .order_by(models.Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        return result.scalars().all()

# Instance وحدة باش نقدرو نستعملوها في الـ Routers
chat_service = ChatService()
