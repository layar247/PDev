from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import Base, User, Topic
from config.conf import ALCHEMY_ENGINE
import os
from survey_data import TOPICS
engine = create_async_engine(ALCHEMY_ENGINE)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_admins()
    await init_topics()

async def init_topics():
    async with async_session() as session:
        # Проверим, нет ли уже тем в базе
        result = await session.execute(select(Topic).limit(1))
        if result.scalars().first():
            return  # уже есть, не перезаписываем
        for t in TOPICS:
            topic = Topic(
                title=t['title'],
                description=t['description'],
                difficulty=t['difficulty'],
                direction=t['direction'],
                weights=t['weights']
            )
            session.add(topic)
        await session.commit()
async def init_admins():
    admin_ids = [int(id_) for id_ in os.getenv("ADMINS", "").split(",") if id_.isdigit()]

    if not admin_ids:
        print("⚠️ Внимание: не указаны ID администраторов в ADMINS!")
        return

    async with async_session() as session:
        for admin_id in admin_ids:
            user = await session.execute(
                select(User).where(User.telegram_id == admin_id)
            )
            user = user.scalar_one_or_none()

            if user:
                if not user.is_admin:
                    user.is_admin = True
                    print(f"Пользователь {admin_id} назначен администратором")
            else:
                new_admin = User(
                    telegram_id=admin_id,
                    is_admin=True
                )
                session.add(new_admin)
                print(f"Создан новый администратор с ID: {admin_id}")

        await session.commit()
