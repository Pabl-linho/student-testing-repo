# app/domains/chat/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# نجبدو الـ Enums لي كرييناهم في الـ Models باش نستعملوهم للـ Validation
from app.domains.chat.models import ChatType, MessageType, RequestStatus


class MessageBase(BaseModel):
    
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(default=MessageType.TEXT)

class MessageCreate(MessageBase):
    # الـ Front-end (Flutter) يبعثلنا الـ chat_id فقط مع المحتوى
    chat_id: int

class MessageResponse(MessageBase):
    # الـ JSON Response لي يرجع للـ Front-end
    id: int
    chat_id: int
    sender_id: Optional[int]  # يقدر يكون Null إذا اليوزر تحذف
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Chat Schemas
# ==========================================
class ChatBase(BaseModel):
    chat_type: ChatType
    name: Optional[str] = Field(None, description="Group name (rah ykon empty fl direct chat)")
    module_id: Optional[int] = Field(None, description="For module communities")

class ChatCreate(ChatBase):
    # نستعملوها كـ Payload كي نحبو نكرييو Chat جديد
    # contact_id نحتاجوها باش نعرفو مع من راح نهضرو في الـ Direct Chat
    contact_id: Optional[int] = None 
    
class ChatResponse(ChatBase):
    id: int
    created_at: datetime  # مهمة للـ Flutter باش يرتب الـ UI
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Chat Request Schemas
# ==========================================
class ChatRequestBase(BaseModel):
    chat_id: int

class ChatRequestCreate(ChatRequestBase):
    """الطالب يبعث طلب باش يدخل لجروب أو يهدر مع Contact"""
    receiver_id: int

class ChatRequestResponse(ChatRequestBase):
    id: int
    sender_id: int
    receiver_id: int
    status: RequestStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)