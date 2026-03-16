# app/domains/chat/router.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from pydantic import ValidationError

from app.core.database import get_db, AsyncSessionLocal
from app.core.security import get_current_user_id, get_current_ws_user_id
from app.domains.chat import schemas
from app.domains.chat.websocket import manager
from app.domains.chat.service import chat_service # استوردنا الـ instance اللي درتها نتا

logger = logging.getLogger(__name__)

def serialize_message(message) -> dict:
    response_schema = schemas.MessageResponse.model_validate(message)
    return response_schema.model_dump(mode="json")

async def send_ws_error(websocket: WebSocket, detail: str, errors: list | None = None):
    payload = {"detail": detail}
    if errors is not None:
        payload["errors"] = errors

    await websocket.send_json({"event": "error", "data": payload})

router = APIRouter(prefix="/chat", tags=["Chat System"])

# ==========================================
# HTTP Endpoints
# ==========================================
@router.get("/{chat_id}/messages", response_model=List[schemas.MessageResponse])
async def get_chat_history(
    chat_id: int, 
    limit: int = 40, 
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id) 
):
    """جلب تاريخ المحادثة للـ Flutter مع Pagination"""
    messages = await chat_service.get_chat_history(
        db=db, 
        chat_id=chat_id, 
        user_id=current_user_id, 
        limit=limit, 
        offset=offset
    )
    return messages

@router.patch("/{chat_id}/messages/{message_id}", response_model=schemas.MessageResponse)
async def update_message(
    chat_id: int,
    message_id: int,
    message_data: schemas.MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    message = await chat_service.update_message(
        db=db,
        chat_id=chat_id,
        message_id=message_id,
        user_id=current_user_id,
        message_data=message_data
    )
    members_ids = await chat_service.get_chat_members_ids(db, chat_id)
    await manager.broadcast_chat_event(
        "message_updated",
        serialize_message(message),
        members_ids
    )
    return message

@router.delete("/{chat_id}/messages/{message_id}", response_model=schemas.MessageResponse)
async def delete_message(
    chat_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    message = await chat_service.delete_message(
        db=db,
        chat_id=chat_id,
        message_id=message_id,
        user_id=current_user_id
    )
    members_ids = await chat_service.get_chat_members_ids(db, chat_id)
    await manager.broadcast_chat_event(
        "message_deleted",
        serialize_message(message),
        members_ids
    )
    return message

# ==========================================
# WebSocket Endpoint
# ==========================================
# زدت user_id في الـ path مؤقتا للتجريب، من بعد تقدر تجبدو من الـ Token
@router.websocket("/ws/{chat_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    chat_id: int,
):
    # 1. نفتحو Session صغيرة للتأكد من الصلاحيات (Security Check)
    async with AsyncSessionLocal() as db:
        try:
            user_id = await get_current_ws_user_id(websocket, db)
            await chat_service.verify_user_in_chat(db, chat_id, user_id)
        except HTTPException:
            await websocket.close(code=1008) # Policy Violation
            return

    # 2. نقبلو الاتصال
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 3. نستناو تطبيق Flutter يبعث رسالة
            data = await websocket.receive_json()
            
            # 4. نفتحو DB Session "فقط" وقت حفظ الرسالة باش ما نضيعوش الـ Connections
            async with AsyncSessionLocal() as db:
                try:
                    # تحويل الـ JSON إلى Pydantic schema
                    message_data = schemas.MessageCreate(**data, chat_id=chat_id)
                    
                    # حفظ الرسالة في PostgreSQL
                    new_message = await chat_service.create_message(
                        db=db, 
                        chat_id=chat_id, 
                        sender_id=user_id, 
                        message_data=message_data
                    )
                    
                    # تحضير الـ Response للـ Frontend
                    response_dict = serialize_message(new_message)
                    
                    # نجيبو أعضاء الـ Group ونبعثولهم الرسالة
                    members_ids = await chat_service.get_chat_members_ids(db, chat_id)
                    await manager.broadcast_chat_event(
                        "message_created",
                        response_dict,
                        members_ids
                    )

                except ValidationError as e:
                    await send_ws_error(websocket, "Invalid message payload", e.errors())
                except HTTPException as e:
                    await send_ws_error(websocket, str(e.detail))
                except Exception as e:
                    await db.rollback()
                    logger.error(f"Error processing message: {e}")
                    await send_ws_error(websocket, "Failed to process message")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
