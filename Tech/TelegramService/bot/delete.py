from sqlalchemy import select, delete
from database.utils import async_session
from database.models import Topic, SurveyAnswer
import asyncio

async def delete_cancel_topic():
    async with async_session() as session:
        result = await session.execute(select(Topic).where(Topic.title == "Отмена"))
        topic = result.scalar_one_or_none()

        if topic:
            await session.execute(delete(SurveyAnswer).where(SurveyAnswer.topic_id == topic.id))
            await session.commit()
            print("❌ Удалены все ответы, связанные с темой 'Отмена'.")

            await session.delete(topic)
            await session.commit()
            print("❌ Удалена тема с названием 'Отмена'.")
        else:
            print("✅ Тема с названием 'Отмена' не найдена.")

asyncio.run(delete_cancel_topic())

