# 🤖 Lesson Counter Bot — Локальная отладка

Локальный симулятор Google Apps Script для отладки бота учета занятий с репетитором.

## 📁 Структура

```
├── src/
│   ├── bot.js          # Логика бота (идентично GAS)
│   ├── test-cli.js     # CLI-тесты без сервера
│   └── server.js       # Express-сервер для webhook
├── shims/              # Эмуляция GAS API
│   ├── SpreadsheetApp.js    # CSV вместо Google Sheets
│   ├── PropertiesService.js # JSON вместо GAS Properties
│   ├── Utilities.js         # Форматирование дат
│   ├── Session.js           # Timezone
│   ├── ContentService.js    # Заглушка
│   ├── UrlFetchApp.js       # HTTP-запросы
│   └── Logger.js            # console.log
├── data/               # Локальные данные (CSV + JSON)
│   ├── Ученики.csv
│   ├── Транзакции.csv
│   ├── Конфиг.csv
│   └── properties.json
└── package.json
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
npm install
```

### 2. CLI-тестирование (без Telegram, самое быстрое)

```bash
npm test
```

Или:

```bash
node src/test-cli.js
```

Это запустит полный набор тестов:
- `/start` — назначение админа
- `/addstudent` — добавление ученика
- `/myid` — получение ID
- `+4` — пополнение баланса
- `meet.google.com/...` — списание занятия
- `/stats` — сводка

После теста в консоли отобразится содержимое всех CSV-файлов.

### 3. Локальный сервер (для реального Telegram)

```bash
npm start
```

Сервер запустится на `http://localhost:3000`.

Чтобы протестировать с реальным Telegram:

1. Установите [ngrok](https://ngrok.com/) или используйте `npx`:
   ```bash
   npx ngrok http 3000
   ```
2. Скопируйте HTTPS-URL от ngrok.
3. Установите webhook:
   ```
   https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=<NGROK_URL>/
   ```

### 4. Установка токена

Если хотите, чтобы бот отправлял реальные сообщения в Telegram (не только логировал в консоль):

**Вариант A — через переменную окружения (рекомендуется):**
```bash
set BOT_TOKEN=123456:ABC...
node src/test-cli.js
```

**Вариант B — через код:**
Раскомментируйте в `src/test-cli.js`:
```javascript
process.env.BOT_TOKEN = "123456:ABC...";
bot.setBotToken();
```

## 🔄 Деплой в Google Apps Script

### ✅ Путь А: Автосборка (рекомендуется)

Всё делается одной командой — код подготовится сам:

```bash
npm run build:gas
```

Это создаст файл `dist/bot.gas.js`, в котором:
- ✅ Убраны Node.js-экспорты
- ✅ Возвращена формула баланса (`=C-D`) для Google Sheets
- ✅ Дата записывается как объект `Date` (не строка)
- ✅ Токен в `setBotToken()` ожидает ручной вставки

**Дальше — 5 шагов:**

1. Откройте `dist/bot.gas.js`, **скопируйте всё содержимое** и вставьте в редактор Google Apps Script (замените старый код целиком).
2. Найдите в самом низу `setBotToken()` и замените `"ВАШ_ТОКЕН_ЗДЕСЬ"` на реальный токен от @BotFather.
3. Нажмите ▶️ на `setBotToken()` — она сохранит токен в лист «Конфиг» таблицы.
4. **Deploy → New deployment → Web app**:
   - **Execute as:** Me
   - **Who has access:** **Anyone** (это критично!)
   - Скопируйте Web App URL (через кнопку 📋, проверьте что нет пробела в конце)
5. Установите webhook в браузере:
   ```
   https://api.telegram.org/bot<ТОКЕН>/setWebhook?url=<ВАШ_WEB_APP_URL>
   ```
   Проверьте:
   ```
   https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo
   ```
   Должно быть `"pending_update_count": 0` и **нет** `last_error_message`.

### 🆘 Путь Б: Откат / выключение

Если нужно быстро остановить бота без удаления кода:
```
https://api.telegram.org/bot<ТОКЕН>/deleteWebhook
```
Чтобы включить обратно — повторите шаг 5 из Пути А.

### 📋 Чек-лист деплоя

| Шаг | Команда / Действие |
|-----|-------------------|
| Тесты зелёные | `npm run test:all` → 14/14 ✅ |
| Сборка готова | `npm run build:gas` |
| Токен вставлен | В `setBotToken()` заменена строка |
| Токен сохранён | ▶️ `setBotToken()` в редакторе GAS |
| Web App деплой | Deploy → Web app → **Anyone** |
| Webhook установлен | `getWebhookInfo` без ошибок |
| Бот отвечает | `/start` в Telegram → приветствие |

## ⚠️ Важные нюансы при деплое

1. **Не забудьте `doGet`** — он уже в коде (возвращает "Bot is running"). Без него Google может отдавать 302.
2. **Anyone в доступе** — иначе Telegram получит 403.
3. **Пробел в URL** — при копировании из Deploy проверьте конец строки. Лучше копируйте через кнопку 📋.
4. **Очистите защиту от дублей** — запустите `clearDuplicateProtection()` в редакторе GAS после первого деплоя.
5. **Если бот молчит** — откройте ⌛ Execution log и ищите красные ошибки.

## 📝 Особенности локальной версии

| GAS API | Локальная замена |
|---------|------------------|
| Google Sheets | CSV-файлы в `data/` |
| PropertiesService | `data/properties.json` |
| UrlFetchApp | `fetch()` (Node.js 18+) |
| Utilities.formatDate | `Intl.DateTimeFormat` |
| Logger.log | `console.log` |

Баланс в локальной версии считается динамически (`bought - spent`), а в GAS — через формулу в ячейке.

## 🛠 Отладка

Все `Logger.log()` из кода выводятся в консоль. Если что-то идет не так — смотрите вывод теста.
