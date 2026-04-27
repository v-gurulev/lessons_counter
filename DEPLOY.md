# 🚀 Чек-лист деплоя — Lesson Counter Bot

> **Цель:** развернуть бота на Render + Supabase и передать готовое решение репетитору.

---

## Что понадобится

| Что | Где взять |
|-----|-----------|
| GitHub-аккаунт | [github.com](https://github.com) |
| Аккаунт Render | [render.com](https://render.com) (регистрация через GitHub) |
| Аккаунт Supabase | [supabase.com](https://supabase.com) |
| Токен бота | @BotFather в Telegram |

---

## Шаг 1. Создать бота в Telegram

1. Напиши [@BotFather](https://t.me/BotFather)
2. Отправь `/newbot`
3. Укажи имя и username бота (например: `LessonCounterBot`)
4. **Сохрани токен** — длинная строка вида `123456789:ABC...`
5. Опционально: загрузи аватарку и описание (`/setuserpic`, `/setdescription`)

---

## Шаг 2. Создать базу данных в Supabase

1. Зайди в [Supabase Dashboard](https://app.supabase.com) → **New project**
2. Дай проекту имя (например, `lesson-counter`)
3. Дождись завершения создания (1-2 минуты)
4. Перейди в раздел **Project Settings → Database**
5. Найди блок **Connection string → URI** (Session Pooler)
6. Скопируй строку подключения:
   ```
   postgresql://postgres.xxx:[PASSWORD]@aws-0-xxx.pooler.supabase.com:5432/postgres
   ```
   > ⚠️ **Важно:** используй именно **Session Pooler** на порту `5432`. Direct connection на порту `5432` к `db.xxx.supabase.co` не заработает на Render free tier из-за IPv6.

---

## Шаг 3. Подготовить репозиторий

У тебя есть два варианта:

### Вариант А: деплоить из папки `python-bot/`

В настройках Render (при создании сервиса) укажи **Root Directory**: `python-bot`

### Вариант Б: деплоить из корня

Файлы `main.py`, `db.py`, `requirements.txt`, `render.yaml` в корне идентичны тем, что в `python-bot/`. Можно деплоить из корня.

**Рекомендация:** используй папку `python-bot/`, чтобы не тащить в деплой лишние файлы (GAS, Node.js, тесты и т.д.).

---

## Шаг 4. Задеплоить на Render

1. В Render нажми **New → Web Service**
2. Подключи свой GitHub-репозиторий
3. Укажи настройки:
   - **Name**: `lesson-counter-bot` (или любое другое)
   - **Runtime**: Python
   - **Root Directory**: `python-bot` (если выбрал вариант А)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free

4. Нажми **Advanced** и добавь Environment Variables:

   | Key | Value | Пример |
   |-----|-------|--------|
   | `BOT_TOKEN` | Токен от @BotFather | `8680311824:AAE...` |
   | `WEBHOOK_URL` | URL будущего сервиса | `https://lesson-counter-bot.onrender.com` |
   | `DATABASE_URL` | URI из Supabase | `postgresql://postgres.xxx...` |
   | `PORT` | `10000` | уже задано в `render.yaml` |

   > 💡 Язык бота (русский/английский) настраивается уже после деплоя командой `/lang` — не нужен отдельный env var.

   > 💡 `WEBHOOK_URL` можно узнать заранее: он будет `https://<имя-сервиса>.onrender.com`

5. Нажми **Create Web Service**
6. Дождись первого деплоя (Build → Deploy). Это занимает 2-5 минут.

---

## Шаг 5. Установить webhook

После успешного деплоя открой в браузере:

```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=<WEBHOOK_URL>
```

**Пример:**
```
https://api.telegram.org/bot8680311824:AAE.../setWebhook?url=https://lesson-counter-bot.onrender.com
```

В ответе должно быть:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

Проверить статус можно тут:
```
https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo
```

---

## Шаг 6. Проверить работу

1. Найди своего бота в Telegram, напиши `/start`
2. Бот должен ответить: *"Вы назначены репетитором (админом)"*
3. Добавь бота в тестовую группу
4. Бот должен приветствовать группу
5. Напиши в группу `+4` от лица админа (если в группе только ты и бот, админ зарегистрируется как ученик в тестовом режиме)
6. Отправь ссылку `meet.google.com/abc-defg-hij` — бот должен списать занятие
7. Напиши боту в личку `/stats` — должна появиться сводка

---

## Шаг 7. Передать репетитору

1. Отправь репетитору файл **[TEACHER_GUIDE.md](TEACHER_GUIDE.md)** (или распечатай / перешли текст)
2. Добавь репетитора админом в группу с ботом (если нужно)
3. Попроси репетитора написать боту `/start` в личные сообщения — он станет админом
4. **Важно:** если ты был админом во время теста, репетитор **не сможет** стать админом, пока не сбросишь админа вручную (через базу данных или `/start` с нового аккаунта)

   Чтобы сбросить админа, выполни в Supabase SQL Editor:
   ```sql
   DELETE FROM config WHERE key = 'ADMIN_CHAT_ID';
   ```

---

## ⚠️ Важные нюансы

### "Засыпание" на бесплатном тарифе
На Render free tier сервис засыпает через ~15 минут бездействия. Первое сообщение после сна будет обрабатываться **30-60 секунд**. Это нормально для бесплатного хостинга.

### Данные не теряются
Supabase хранит данные постоянно. Даже если Render перезапустит сервер — все ученики, балансы и транзакции останутся на месте.

### Не используй SQLite на Render
Если не задать `DATABASE_URL` — бот переключится на SQLite, и файл `bot.db` будет создаваться локально на Render. При каждом перезапуске (а free tier перезапускается часто) данные **обнулятся**.

### Если бот перестал отвечать
1. Проверь статус в Render Dashboard (Logs)
2. Перезапусти сервис вручную: Render → свой сервис → **Manual Deploy → Deploy latest commit**
3. Проверь webhook через `getWebhookInfo` (см. шаг 5)

---

## 📁 Структура для деплоя

```
python-bot/
├── main.py           # Логика бота
├── db.py             # База данных (SQLite / Postgres / Sheets)
├── requirements.txt  # Зависимости
├── render.yaml       # Blueprint для Render (опционально)
└── test_bot.py       # Тесты (не деплоятся, но полезны)
```

---

Готово! После выполнения всех шагов бот работает и готов к передаче репетитору.
