# Kursovichok Bot — Telegram‑бот для выбора темы курсовой работы

Telegram‑бот помогает студентам ФКТиПМ КубГУ выбрать тему курсовой работы через опрос с весовыми коэффициентами. Администраторы могут полностью управлять темами(CRUD), просматривать список тем и импортировать их через Excel.

Всё работает в Docker Compose: сам бот на `aiogram 3`, PostgreSQL для хранения данных и Redis для FSM.

### Запуск через Docker Compose 

```bash
git clone <your-repo-url>
cd kursovichok-bot
# Отредактируйте .env (укажите BOT_TOKEN, ADMIN_IDS и т.д.)
docker compose up --build

##Локальный запуск

```python -m venv venv
source venv/bin/activate  # или .\venv\Scripts\activate на Windows
pip install -r requirements.txt
cp .env.example .env
# Настройте подключение к PostgreSQL (локальный или через Docker)
python main.py```
