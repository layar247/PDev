import psycopg2
from psycopg2.extras import DictCursor
from sqlalchemy import create_engine
from models import Base

DB_PARAMS = {
    'host': 'localhost',
    'database': 'nes',
    'user': 'postgres',
    'password': '12345'
}

def init_db():
    engine = create_engine(f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}/{DB_PARAMS['database']}")
    Base.metadata.create_all(engine)
    print("Таблицы созданы (или уже существуют)")

def get_connection():
    return psycopg2.connect(**DB_PARAMS, cursor_factory=DictCursor)

def fetch_all(query, params=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

def execute_query(query, params=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()