from sqlalchemy import Float,Numeric,Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from decimal import Decimal
from sqlalchemy import TypeDecorator

Base = declarative_base()

class NumericArray(TypeDecorator):
    impl = ARRAY(Numeric(3, 2))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return [Decimal(str(v)).quantize(Decimal('0.01')) for v in value]  # округление до 2 знаков
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return [Decimal(str(v)).quantize(Decimal('0.01')) for v in value]
        return value

class SurveyAnswer(Base):
    __tablename__ = 'survey_answers'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer)
    answer_idx = Column(Integer)
    user = relationship("User", back_populates="answers")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    full_name = Column(String(100))
    username = Column(String(50))
    is_admin = Column(Boolean, default=False)
    answers = relationship("SurveyAnswer", back_populates="user")

class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    difficulty = Column(String(20))
    direction = Column(String(50))
    weights = Column(NumericArray)


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    options = Column(ARRAY(String))
    weights = Column(NumericArray)