# Kursovichok Bot — Telegram‑бот для выбора темы курсовой работы

Telegram‑бот помогает студентам ФКТиПМ КубГУ выбрать тему курсовой работы через опрос с весовыми коэффициентами. Администраторы могут полностью управлять темами(CRUD), просматривать список тем и импортировать их через Excel.

Всё работает в Docker Compose: сам бот на `aiogram 3`, PostgreSQL для хранения данных и Redis для FSM.

## 🚀 Запуск

### Запуск через Docker Compose 

```bash
git clone <your-repo-url>
cd kursovichok-bot
# Отредактируйте .env (укажите BOT_TOKEN, ADMIN_IDS и т.д.)
docker compose up --build
```
### Локальный запуск
```
python -m venv venv
source venv/bin/activate  #или .\venv\Scripts\activate на Windows
pip install -r requirements.txt
cp .env.example .env
#Настройте подключение к PostgreSQL (локальный или через Docker)
python main.py
```
### Порты и сервисы

| Сервис | URL | Назначение |
| --- | --- | --- |
| Bot | (нет внешнего порта) | Обработка команд и опросов |
| PostgreSQL | `localhost:5432` | Хранение пользователей, тем, ответов |
| TEI embeddings | `localhost:6379` | Хранение состояний FSM |

### Сетевые доступы для установки
Для работы бота на сервере нужны исходящие HTTPS‑доступы:

| Адрес | Для чего нужен |
| --- | --- |
| https://api.telegram.org | `Все запросы к Telegram Bot API` |
| https://registry-1.docker.io | `Скачивание базовых образов (PostgreSQL, Redis, Python)` |
| https://auth.docker.io | `http://localhost:8090/v1` |
| https://pypi.org | `Установка Python‑пакетов (если собираете образ локально)` |
| https://files.pythonhosted.org | `Файлы пакетов PyPI` |


