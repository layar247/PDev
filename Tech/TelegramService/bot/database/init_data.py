from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Question, Topic
from survey_data import SURVEY_QUESTIONS, TOPICS
import time


def init_survey_data():
    max_retries = 5
    retry_delay = 2

    for i in range(max_retries):
        try:
            engine = create_engine("postgresql://postgres:megasecretpassword@db/db")
            engine.connect()
            break
        except Exception as e:
            if i == max_retries - 1:
                print("Не удалось подключиться к БД!")
                return
            print(f"Попытка {i + 1}/{max_retries} - БД не доступна, ждем...")
            time.sleep(retry_delay)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        Base.metadata.create_all(engine)
        if not session.query(Question).first():
            for q in SURVEY_QUESTIONS:
                session.add(Question(**q))
            for t in TOPICS:
                session.add(Topic(**t))

            session.commit()
            print("✅ Данные успешно загружены в БД")
        else:
            print("ℹ️ Данные уже существуют в БД, пропускаем инициализацию")

    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при загрузке данных: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_survey_data()