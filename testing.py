import asyncio
from app.core.database import engine, Base, AsyncSessionLocal

from app.domains.users.models import User, PrivacySettings, Contact
from app.domains.chat.models import Chat, ChatMember, Message, ChatRequest, ChatType, MemberRole


async def init_db():
    print("⏳ Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created.")

    print("⏳ Seeding dummy data...")
    async with AsyncSessionLocal() as db:
        user1 = User(username="ahmed", email="ahmed@univ.dz", hashed_password="pwd")
        user2 = User(username="mohamed", email="mohamed@univ.dz", hashed_password="pwd")
        user3 = User(username="yacine", email="yacine@univ.dz", hashed_password="pwd")

        db.add_all([user1, user2, user3])
        await db.commit()

        await db.refresh(user1)
        await db.refresh(user2)
        await db.refresh(user3)

        private_chat = Chat(chat_type=ChatType.DIRECT)
        db.add(private_chat)
        await db.commit()
        await db.refresh(private_chat)

        db.add_all([
            ChatMember(chat_id=private_chat.id, user_id=user1.id, role=MemberRole.MEMBER),
            ChatMember(chat_id=private_chat.id, user_id=user2.id, role=MemberRole.MEMBER),
        ])

        group_chat = Chat(chat_type=ChatType.GROUP, name="Dev Team")
        db.add(group_chat)
        await db.commit()
        await db.refresh(group_chat)

        db.add_all([
            ChatMember(chat_id=group_chat.id, user_id=user1.id, role=MemberRole.OWNER),
            ChatMember(chat_id=group_chat.id, user_id=user2.id, role=MemberRole.ADMIN),
            ChatMember(chat_id=group_chat.id, user_id=user3.id, role=MemberRole.MEMBER),
        ])

        await db.commit()

        print(f"✅ Data seeded! Users IDs: ({user1.id}, {user2.id}, {user3.id})")
        print(f"✅ Private Chat ID: {private_chat.id} | Group Chat ID: {group_chat.id}")


if __name__ == "__main__":
    asyncio.run(init_db())