# 🤖 Lesson Counter Bot

Бот для учёта занятий с репетитором. Работает на Python, хранит данные в **Supabase PostgreSQL** (надёжно, не теряются при перезапусках), хостится на Render.com.

Поддерживает два языка: **русский** и **английский**. Админ переключает язык командой `/lang`.

---

## 🚀 Быстрый старт (для нового владельца)

1. Зарегистрируйся на [render.com](https://render.com) через GitHub
2. Создай проект в [Supabase](https://supabase.com)
3. Задеплой бота по инструкции из [DEPLOY.md](DEPLOY.md)
4. Передай репетитору [TEACHER_GUIDE.md](TEACHER_GUIDE.md)

---

## 📁 Структура проекта

```
.
├── main.py           # Точка входа, хендлеры Telegram
├── db.py             # Абстракция БД: SQLite / Postgres / Google Sheets
├── i18n.py           # Локализация (ru / en)
├── test_bot.py       # 36 unit-тестов (async, SQLite backend)
├── requirements.txt  # Зависимости
├── runtime.txt       # Версия Python для Render
├── render.yaml       # Blueprint для Render
├── DEPLOY.md         # Чек-лист деплоя (для разработчика)
├── TEACHER_GUIDE.md  # Инструкция для репетитора
└── AGENTS.md         # Архитектура и соглашения
```

---

## 📝 Функционал

- `/start` — назначение админа
- `/lang ru|en` — смена языка (только админ)
- `/register` (reply на сообщение ученика) — добавить ученика в группе
- `/addstudent [chat_id] [group_chat_id] [Имя]` — добавить ученика вручную
- `/deletestudent [chat_id]` — удалить ученика
- `/stats` — сводка по всем ученикам
- `/myid` — узнать chat_id или ID группы
- `+4` — пополнение баланса
- `meet.google.com/...` — списание занятия
- Авто-регистрация ученика при первом сообщении в группе
- Тестовый режим: если в группе только админ + бот, админ = ученик

---

## 🗄️ База данных

Фабрика `get_db()` выбирает backend по env vars:

| Env var | Backend |
|---------|---------|
| `DATABASE_URL` | `PostgresDB` (Supabase) — **основной для продакшена** |
| `GOOGLE_SHEET_ID` + `GOOGLE_CREDENTIALS` | `SheetsDB` (резерв) |
| ничего | `SQLiteDB` (файл `bot.db`) — только для тестов |

---

## ✅ Тесты

```bash
python -m unittest test_bot -v
```

36 тестов покрывают все сценарии: пополнение, списание, авто-регистрацию, локализацию, edge cases.

---

## 🛠️ Стек

- Python 3.14+, async/await
- python-telegram-bot 22.x (webhooks)
- psycopg2-binary + Supabase PostgreSQL
- aiosqlite (для локальных тестов)
