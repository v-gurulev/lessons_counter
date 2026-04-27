# 📋 Пошаговая инструкция: Google Sheets для бота

Это руководство для человека, который будет вести бота. **Никакого программирования не нужно.**

---

## Шаг 1. Создать Google Таблицу

1. Открой браузер и зайди в свой Google-аккаунт
2. Перейди по ссылке: https://sheets.new
3. Создастся пустая таблица. Назови её, например: `Учёт занятий — бот`
4. **Сохрани URL таблицы** — он понадобится позже. Выглядит так:
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
   ```
   **Часть после `/d/` и до `/edit` — это `GOOGLE_SHEET_ID`.**
   В примере выше: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

---

## Шаг 2. Создать листы в таблице

По умолчанию есть один лист `Sheet1`. Переименуй его и создай ещё два.

### Лист 1: `Config`
Кликни правой кнопкой на ярлык листа внизу → **Rename** → напиши `Config`

В ячейки введи заголовки:

| A | B |
|---|---|
| `key` | `value` |

### Лист 2: `Students`
Нажми на `+` (плюс) внизу → создастся новый лист → переименуй в `Students`

В ячейки введи заголовки (первая строка):

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| `chat_id` | `name` | `group_chat_id` | `bought` | `spent` | `last_lesson_date` |

### Лист 3: `Transactions`
Создай ещё один лист → переименуй в `Transactions`

В ячейки введи заголовки:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| `id` | `date` | `chat_id` | `name` | `type` | `count` | `note` |

---

## Шаг 3. Создать проект в Google Cloud

1. Перейди по ссылке: https://console.cloud.google.com/
2. Нажми сверху на селектор проекта (выпадающий список рядом с логотипом Google Cloud)
3. Нажми **New Project**
4. В поле **Project name** напиши: `lesson-counter-bot`
5. Нажми **Create**
6. Подожди 5–10 секунд, пока проект создастся

---

## Шаг 4. Включить Google Sheets API

1. Убедись, что сверху выбран проект `lesson-counter-bot`
2. В левом меню нажди на **APIs & Services** → **Library**
3. В строке поиска напиши: `Google Sheets API`
4. Нажми на **Google Sheets API** в результатах
5. Нажми синюю кнопку **Enable**
6. Подожди, пока включится (обычно мгновенно)

---

## Шаг 5. Создать Service Account

1. В левом меню нажди **APIs & Services** → **Credentials**
2. Нажми сверху **+ Create Credentials** → **Service Account**
3. На шаге **Service account details**:
   - **Service account name**: `lesson-bot`
   - **Service account ID** заполнится автоматически
   - Нажми **Create and Continue**
4. На шаге **Grant this service account access to project**:
   - Роль: выбери **Basic** → **Editor**
   - Нажми **Continue**
5. На шаге **Grant users access to this service account**:
   - Ничего не добавляй
   - Нажми **Done**

---

## Шаг 6. Создать JSON-ключ (credentials)

1. Ты снова на странице **Credentials**
2. В разделе **Service Accounts** найди созданный аккаунт `lesson-bot` и нажми на него
3. Перейди во вкладку **Keys**
4. Нажми **Add Key** → **Create new key**
5. Выбери тип **JSON**
6. Нажми **Create**
7. **Файл скачается автоматически** (например, `lesson-bot-123456.json`). **Не потеряй его!**

---

## Шаг 7. Получить `client_email`

Открой скачанный JSON-файл любым текстовым редактором (Блокнот, Notepad++). Найди поле:

```json
"client_email": "lesson-bot@lesson-counter-bot.iam.gserviceaccount.com"
```

**Скопируй это значение целиком.** Это email сервисного аккаунта.

---

## Шаг 8. Поделиться таблицей с сервисным аккаунтом

1. Вернись в свою Google Таблицу (`Учёт занятий — бот`)
2. Нажми кнопку **Share** (справа вверху)
3. В поле **Add people** вставь скопированный `client_email`:
   ```
   lesson-bot@lesson-counter-bot.iam.gserviceaccount.com
   ```
4. Убедись, что права стоят **Editor** (Редактор)
5. Нажми **Send** или **Share**

---

## Шаг 9. Подготовить `GOOGLE_CREDENTIALS`

Открой скачанный JSON-файл в текстовом редакторе. **Выдели весь текст файла** (Ctrl+A) и **скопируй** (Ctrl+C).

Это и есть значение для переменной `GOOGLE_CREDENTIALS`.

> ⚠️ Это секретный ключ! Не показывай его никому и не выкладывай в открытый доступ.

---

## Шаг 10. Задеплоить на Render

1. Зайди на https://render.com
2. Нажми **New → Web Service**
3. Подключи GitHub-репозиторий `v-gurulev/lessons_counter`
4. Настройки:
   - **Name**: `lesson-counter-bot` (или любое другое)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. Прокрути вниз до **Environment Variables** и нажми **Add Environment Variable**
6. Добавь переменные:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Твой токен от @BotFather |
| `WEBHOOK_URL` | `https://lesson-counter-bot.onrender.com` |
| `GOOGLE_SHEET_ID` | ID таблицы из шага 1 |
| `GOOGLE_CREDENTIALS` | Весь JSON-текст из шага 9 |

7. Нажми **Create Web Service**
8. Дождись, пока статус станет **Live**

---

## Шаг 11. Установить webhook

Открой в браузере:
```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://lesson-counter-bot.onrender.com
```

Замени `<BOT_TOKEN>` на свой реальный токен.

Должен прийти ответ:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

---

## ✅ Готово!

Бот работает, данные хранятся в Google Таблице. Можешь открыть таблицу в любой момент и посмотреть:
- **Students** — список учеников и баланс
- **Transactions** — все операции (пополнения и списания)
- **Config** — настройки (например, кто админ)

---

## 🆘 Если что-то пошло не так

**Бот не отвечает:**
- Проверь логи на Render (вкладка **Logs**)
- Убедись, что webhook установлен: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

**Ошибка `Google credentials not found`:**
- Перепроверь, что `GOOGLE_CREDENTIALS` содержит ВЕСЬ JSON, включая фигурные скобки `{ }`

**Ошибка доступа к таблице:**
- Убедись, что в шаге 8 ты поделился таблицей именно с `client_email` из JSON-файла
- Убедись, что права стоят **Editor**, не **Viewer**
