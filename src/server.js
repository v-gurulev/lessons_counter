// ==================== ЛОКАЛЬНЫЙ СЕРВЕР (Express) ====================
// Запуск: node src/server.js
// Сервер слушает POST-запросы на / и имитирует GAS webhook
// Для тестирования с реальным Telegram нужен ngrok или аналог

// Подключаем shim'ы как глобальные объекты (как в GAS)
global.SpreadsheetApp = require('../shims/SpreadsheetApp');
global.PropertiesService = require('../shims/PropertiesService');
global.Utilities = require('../shims/Utilities');
global.Session = require('../shims/Session');
global.ContentService = require('../shims/ContentService');
global.UrlFetchApp = require('../shims/UrlFetchApp');
global.Logger = require('../shims/Logger');

const express = require('express');
const bot = require('./bot');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
  const result = bot.doGet(req);
  res.status(200).send(result.getContent());
});

app.post('/', (req, res) => {
  try {
    const event = {
      postData: {
        contents: JSON.stringify(req.body)
      }
    };
    const result = bot.doPost(event);
    res.status(200).send(result.getContent());
  } catch (err) {
    console.error('❌ Ошибка в doPost:', err);
    res.status(500).send('Error');
  }
});

app.listen(PORT, () => {
  console.log('============================================');
  console.log(`🤖 Бот слушает на http://localhost:${PORT}`);
  console.log('============================================');
  console.log('Для теста отправьте POST-запрос на /');
  console.log('Для реального Telegram webhook используйте ngrok:');
  console.log('  npx ngrok http ' + PORT);
  console.log('Затем установите webhook:');
  console.log('  https://api.telegram.org/bot<TOKEN>/setWebhook?url=<NGROK_URL>');
  console.log('============================================');
});
