# 📋 Supabase PostgreSQL — инструкция для России

Google Cloud не работает из РФ без VPN/иностранной карты.  
**Supabase** — бесплатная альтернатива, работает из России через GitHub-авторизацию.

---

## Шаг 1. Регистрация на Supabase

1. Открой: https://supabase.com
2. Нажми **Start your project**
3. Выбери **Continue with GitHub**
4. Авторизуйся через свой GitHub-аккаунт

---

## Шаг 2. Создать проект

1. После входа нажми **New project**
2. **Organization**: выбери свою (или создай)
3. **Project name**: `lesson-counter`
4. **Database password**: нажми **Generate a password** — Supabase сгенерирует сложный пароль
5. **Region**: оставь `Europe` (ближайший к РФ)
6. Нажми **Create new project**
7. Подожди 1–2 минуты, пока проект создастся

---

## Шаг 3. Получить connection string

1. На главной странице проекта найди секцию **"Get connected"**
2. Нажми плитку **Direct** (Connection string)
3. Убедись, что выбран тип **URI**
4. Скопируй строку вида:
   ```
   postgresql://postgres:PASSWORD@db.xxxxxx.supabase.co:5432/postgres
   ```

---

## Шаг 4. Задеплоить бота на Render

1. Зайди на https://render.com
2. Открой свой Web Service `lesson-counter-bot`
3. Перейди во вкладку **Environment**
4. Добавь переменную:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://postgres:PASSWORD@db.xxxxxx.supabase.co:5432/postgres` |

5. Нажми **Save Changes** — Render автоматически перезапустит сервис

> **Важно:** таблицы создаются автоматически при первом запуске бота (`PostgresDB.init()`). Ручной SQL не требуется.

---

## Шаг 5. Проверить webhook

```
https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo
```

`pending_update_count` должен быть `0`, а `url` должен совпадать с твоим Render-URL.

---

## ✅ Готово!

Данные хранятся в Supabase PostgreSQL. Чтобы посмотреть таблицы:
1. Зайди в проект на Supabase
2. В левом меню **Table Editor**
3. Видишь таблицы `students`, `transactions`, `config` — можешь править прямо в браузере

---

## 🆘 Проблемы

**Ошибка подключения к базе:**
- Проверь, что в `DATABASE_URL` правильный пароль (без скобок `[YOUR-PASSWORD]`)
- Убедись, что в строке `postgresql://`, а не `postgres://`

**Render не видит DATABASE_URL:**
- Перепроверь, что переменная добавлена в Environment Variables
- Перезапусти сервис вручную (кнопка **Manual Deploy**)

**Таблицы не создались:**
- Проверь логи Render (вкладка **Logs**) — там будет текст ошибки
- Убедись, что `asyncpg` установлен (`pip install asyncpg`)
