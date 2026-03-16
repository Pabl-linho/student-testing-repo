
# app/domains/chat/models.py
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

from app.domains.users.models import User

class ChatType(str, enum.Enum):
    DIRECT = "DIRECT"               
    GROUP = "GROUP"                
    MODULE_COMMUNITY = "MODULE_COMMUNITY"  

class MemberRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

class MessageType(str, enum.Enum):
    TEXT = "TEXT"                   # فكرة الـ presigned URLs للصور ممتازة جداً (AWS S3 / MinIO)
    IMAGE = "IMAGE"                 
    DOCUMENT = "DOCUMENT"

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # بالنسبة لملاحظتك: نعم، هكذا خير. جدول واحد للـ Chats يسهل بزاف الـ Queries للـ Front-end (Flutter)
    chat_type: Mapped[ChatType] = mapped_column(SQLEnum(ChatType), nullable=False)   
    
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True) 
    module_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships 
    members: Mapped[list["ChatMember"]] = relationship("ChatMember", back_populates="chat", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    requests: Mapped[list["ChatRequest"]] = relationship("ChatRequest", back_populates="chat", cascade="all, delete-orphan")

class ChatMember(Base):    
    __tablename__ = "chat_members"
    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_member"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ondelete="CASCADE" تخدم روعة مع PostgreSQL لتنظيف البيانات تلقائياً
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[MemberRole] = mapped_column(SQLEnum(MemberRole), default=MemberRole.MEMBER)
    
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="chat_memberships", foreign_keys=[user_id]) 

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(SQLEnum(MessageType), default=MessageType.TEXT)
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    sender: Mapped[Optional["User"]] = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])

class ChatRequest(Base):
    __tablename__ = "chat_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True) # تم تصحيح هذا السطر
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False) 
    
    status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["Chat"] = relationship("Chat", back_populates="requests")
    sender: Mapped["User"] = relationship("User", back_populates="sent_chat_requests", foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", back_populates="received_chat_requests", foreign_keys=[receiver_id])
