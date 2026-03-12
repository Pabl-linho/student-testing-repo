import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GroupAddPermission(str, enum.Enum):          # UserPrivacy
    EVERYONE = "EVERYONE"
    CONTACTS_ONLY = "CONTACTS_ONLY"
    NOBODY = "NOBODY"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
           
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # ban or delete
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 1 to 1 relationship: 
    privacy_settings: Mapped["PrivacySettings"] = relationship(
        "PrivacySettings", 
        back_populates="user", 
        uselist=False, # 1 to 1 in SQLAlchemy
        cascade="all, delete-orphan"
    )
    #?? --------- l import hna for create a relationship 
    
    # messages: Mapped[list["Message"]] = relationship("Message", back_populates="sender")


class PrivacySettings(Base):

    __tablename__ = "privacy_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    who_can_add_me_to_groups: Mapped[GroupAddPermission] = mapped_column(
        SQLEnum(GroupAddPermission), 
        default=GroupAddPermission.EVERYONE
    )
    
    user: Mapped["User"] = relationship("User", back_populates="privacy_settings")


class Contact(Base):
   
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    #---------- mch lazam ykon contact ''''' ??
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # cannot add the same user twice in db ( for checkiing )

    __table_args__ = (
        UniqueConstraint('user_id', 'contact_id', name='uq_user_contact'),
    )