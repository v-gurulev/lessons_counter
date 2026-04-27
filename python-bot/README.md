# 🤖 Lesson Counter Bot — Python + Google Sheets + Render.com

Бот для учета занятий с репетитором. Работает на Python, хранит данные в **Google Sheets** (не теряются при перезапусках), хостится на Render.com.

---

## 🚀 Быстрый старт (для нового владельца)

### 1. Создать Google Таблицу
1. Открой [Google Sheets](https://sheets.new)
2. Создай пустую таблицу
3. Поделись доступом с сервисным аккаунтом (см. шаг 3)

### 2. Создать Google Service Account
1. Перейди в [Google Cloud Console](https://console.cloud.google.com/)
2. Создай проект → включи **Google Sheets API**
3. **IAM & Admin** → **Service Accounts** → **Create**
4. Скачай JSON-ключ (`credentials.json`)
5. Скопируй **весь JSON как текст** — он понадобится для Render

### 3. Поделиться таблицей
В Google Sheets нажми **Share** → вставь email сервисного аккаунта (из `credentials.json`, поле `client_email`)

### 4. Задеплоить на Render
1. Зарегистрируйся на [render.com](https://render.com) через GitHub
2. **New → Web Service** → подключи этот репозиторий
3. Настройки:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
4. Добавь Environment Variables:

| Key | Value | Описание |
|-----|-------|----------|
| `BOT_TOKEN` | `8680311824:AAE...` | Токен от @BotFather |
| `WEBHOOK_URL` | `https://your-bot.onrender.com` | URL сервиса |
| `GOOGLE_SHEET_ID` | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` | ID таблицы из URL |
| `GOOGLE_CREDENTIALS` | `{...весь JSON...}` | Весь JSON из credentials.json |

5. Нажми **Create Web Service**

### 5. Установить webhook
```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-bot.onrender.com
```

---

## 📁 Структура проекта

```
python-bot/
├── main.py           # Логика бота (handlers)
├── db.py             # База данных: SQLite или Google Sheets
├── test_bot.py       # 32 теста
├── requirements.txt  # Зависимости
├── render.yaml       # Blueprint для Render
└── README.md         # Этот файл
```

## 📝 Функционал

- `/start` — назначение админа
- `/register` (reply на сообщение ученика) — добавить ученика в группе
- `/addstudent [chat_id] [group_chat_id] [Имя]` — добавить ученика вручную
- `/deletestudent [chat_id]` — удалить ученика
- `/stats` — сводка по всем ученикам
- `/myid` — узнать chat_id или ID группы
- `+4` — пополнение баланса
- `meet.google.com/...` — списание занятия
- Авто-регистрация ученика при первом сообщении в группе
- Тестовый режим: если в группе только админ + бот, админ = ученик

## 🗄️ Где хранятся данные

Если задан `GOOGLE_SHEET_ID` — данные в **Google Sheets** (3 листа: Config, Students, Transactions).

Если НЕ задан — используется **SQLite** локально (для тестов).

---

## ✅ Тесты

```bash
python -m unittest test_bot -v
```

32 теста покрывают все сценарии: пополнение, списание, авто-регистрацию, edge cases.
