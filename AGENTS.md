<!-- AGENTS.md — Lesson Counter Bot -->

## Стек

- **Python 3.14+**, async/await
- **python-telegram-bot** 22.x (webhooks)
- **База данных**: Supabase PostgreSQL (production) / SQLite (local tests) / Google Sheets (legacy)
- **Драйвер БД**: `psycopg2-binary` (через `asyncio.to_thread`) + `aiosqlite`
- **Хостинг**: Render.com free tier (webhook mode)
- **Локализация**: `i18n.py` — ru/en, переключается админом через `/lang`

## Структура проекта

```
.
├── main.py              # Точка входа, хендлеры Telegram
├── db.py                # Абстракция БД: SQLiteDB / PostgresDB / SheetsDB
├── i18n.py              # Локализация: TRANSLATIONS + _() + get_lang()
├── test_bot.py          # 36 unit-тестов (async, SQLite backend)
├── requirements.txt     # Зависимости
├── render.yaml          # Blueprint для Render
├── DEPLOY.md            # Чек-лист деплоя
├── TEACHER_GUIDE.md     # Инструкция для репетитора
└── README.md            # Обзор проекта
```

## Архитектура БД

Фабрика `get_db()` выбирает backend по env vars:

| Env var | Backend |
|---------|---------|
| `DATABASE_URL` | `PostgresDB` (Supabase) |
| `GOOGLE_SHEET_ID` + `GOOGLE_CREDENTIALS` | `SheetsDB` |
| ничего | `SQLiteDB` (файл `bot.db`) |

**Таблицы** (авто-создаются при `db.init()`):
- `config(key TEXT PRIMARY KEY, value TEXT)` — admin_id, language и др.
- `students(id, chat_id, name, group_chat_id, bought, spent, last_lesson_date)`
- `transactions(id, date, chat_id, name, type, count, note)`

## Локализация

Все строки вынесены в `i18n.py`. В хендлерах используется:

```python
from i18n import _, get_lang

lang = await get_lang()
await update.message.reply_text(_("key", lang, name="..."))
```

- По умолчанию язык `ru`
- Хранится в `config.language`
- Меняется админом: `/lang ru` или `/lang en`

## Ключевые env vars (Render)

```
BOT_TOKEN=<токен от @BotFather>
WEBHOOK_URL=https://lessons-counter.onrender.com
DATABASE_URL=postgresql://postgres.xxx:[PASSWORD]@aws-0-xxx.pooler.supabase.com:5432/postgres
PORT=10000
```

> **Важно:** Supabase Session Pooler использует порт **5432** (не Direct connection на 5432 к `db.xxx.supabase.co`). Render free tier не поддерживает IPv6 — поэтому только Session Pooler.

## Тесты

```bash
python test_bot.py   # 36 тестов, SQLite backend
```

Все тесты мокают Telegram Update/Context. Для Postgres/Google Sheets тестов нет — тестируется только SQLite backend.

## Особенности Telegram

- **Бот должен быть админом в группе** с правом "Read messages" — иначе не видит обычные сообщения.
- **При добавлении в группу** бот отправляет приветствие и авто-регистрирует первого написавшего.
- **Админ в группе ≤2 человек** может тестировать бота как "ученик".
- **Markdown парсинг** отключён в `myid_handler` и welcome-сообщениях — избегать `parse_mode="Markdown"` там, где есть риск спецсимволов.

## Деплой

1. Push в `main` на GitHub
2. Render → Manual Deploy → Clear build cache & deploy
3. Проверить webhook: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

## Частые проблемы

| Проблема | Решение |
|----------|---------|
| `Network is unreachable` к Supabase | Использовать Session Pooler, не Direct connection |
| `asyncpg.exceptions.InternalServerError: max clients reached` | Перейти на `psycopg2-binary` (открывать/закрывать соединение на запрос) |
| Render деплоит старый код | Проверить ветку в Settings, сделать Clear build cache & deploy |
| SQLite данные теряются | Установить `DATABASE_URL` → будет PostgreSQL |
