// ==================== ЛОКАЛЬНЫЙ CLI-ТЕСТЕР ====================
// Запуск: node src/test-cli.js
// Имитирует запросы от Telegram без реального сервера и webhook

// Подключаем shim'ы как глобальные объекты (как в GAS)
global.SpreadsheetApp = require('../shims/SpreadsheetApp');
global.PropertiesService = require('../shims/PropertiesService');
global.Utilities = require('../shims/Utilities');
global.Session = require('../shims/Session');
global.ContentService = require('../shims/ContentService');
global.UrlFetchApp = require('../shims/UrlFetchApp');
global.Logger = require('../shims/Logger');

const bot = require('./bot');
const fs = require('fs');
const path = require('path');

function makeEvent(updateId, chatId, text, firstName = "TestUser") {
  return {
    postData: {
      contents: JSON.stringify({
        update_id: updateId,
        message: {
          message_id: 1,
          from: {
            id: parseInt(chatId),
            first_name: firstName,
            is_bot: false
          },
          chat: {
            id: parseInt(chatId),
            first_name: firstName,
            type: "private"
          },
          date: Math.floor(Date.now() / 1000),
          text: text
        }
      })
    }
  };
}

function showCsv(name) {
  const filePath = path.join(__dirname, '..', 'data', `${name}.csv`);
  if (!fs.existsSync(filePath)) {
    console.log(`\n📄 ${name}.csv — файл не существует`);
    return;
  }
  const content = fs.readFileSync(filePath, 'utf8');
  console.log(`\n📄 ${name}.csv:`);
  console.log(content || '(пусто)');
}

async function runTests() {
  console.log('============================================');
  console.log('🚀 ЗАПУСК ЛОКАЛЬНЫХ ТЕСТОВ БОТА');
  console.log('============================================\n');

  const ADMIN_CHAT_ID = "320246687";

  // 1. Очистка защиты от дублей
  console.log('🧹 Очистка защиты от дублей...');
  bot.clearDuplicateProtection();

  // 2. Установка токена (опционально, для реальных запросов в Telegram)
  // Если хотите тестировать с реальным ботом, раскомментируйте и вставьте токен:
  // process.env.BOT_TOKEN = "123456:ABC...";
  // bot.setBotToken();

  // 3. Тест: /start админом
  console.log('\n📝 Тест 1: /start от админа (chat_id=' + ADMIN_CHAT_ID + ')');
  let result = bot.doPost(makeEvent(1000001, ADMIN_CHAT_ID, "/start"));
  console.log('Ответ бота:', result.getContent());

  // 4. Тест: /addstudent
  console.log('\n📝 Тест 2: /addstudent ' + ADMIN_CHAT_ID + ' ТестовыйУченик');
  result = bot.doPost(makeEvent(1000002, ADMIN_CHAT_ID, "/addstudent " + ADMIN_CHAT_ID + " ТестовыйУченик"));
  console.log('Ответ бота:', result.getContent());

  // 5. Тест: /myid
  console.log('\n📝 Тест 3: /myid');
  result = bot.doPost(makeEvent(1000003, ADMIN_CHAT_ID, "/myid"));
  console.log('Ответ бота:', result.getContent());

  // 6. Тест: пополнение (+4)
  console.log('\n📝 Тест 4: пополнение на 4 занятия (текст: "+4")');
  result = bot.doPost(makeEvent(1000004, ADMIN_CHAT_ID, "+4"));
  console.log('Ответ бота:', result.getContent());

  // 7. Тест: ссылка на Meet (списание)
  console.log('\n📝 Тест 5: ссылка на Google Meet (meet.google.com/abc-defg-hij)');
  result = bot.doPost(makeEvent(1000005, ADMIN_CHAT_ID, "meet.google.com/abc-defg-hij"));
  console.log('Ответ бота:', result.getContent());

  // 8. Тест: /stats
  console.log('\n📝 Тест 6: /stats (сводка)');
  result = bot.doPost(makeEvent(1000006, ADMIN_CHAT_ID, "/stats"));
  console.log('Ответ бота:', result.getContent());

  // 9. Показываем содержимое CSV
  console.log('\n============================================');
  console.log('📊 СОСТОЯНИЕ БАЗЫ ДАННЫХ');
  console.log('============================================');
  showCsv('Конфиг');
  showCsv('Ученики');
  showCsv('Транзакции');

  console.log('\n============================================');
  console.log('✅ ТЕСТЫ ЗАВЕРШЕНЫ');
  console.log('============================================');
}

runTests().catch(err => {
  console.error('❌ Ошибка при выполнении тестов:', err);
  process.exit(1);
});
