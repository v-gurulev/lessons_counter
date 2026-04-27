// ==================== ПОЛНЫЙ НАБОР ТЕСТОВ ====================
// Запуск: node tests/run-all.js

const fs = require('fs');
const path = require('path');

// --- Подключаем shims как глобальные объекты ---
global.SpreadsheetApp = require('../shims/SpreadsheetApp');
global.PropertiesService = require('../shims/PropertiesService');
global.Utilities = require('../shims/Utilities');
global.Session = require('../shims/Session');
global.ContentService = require('../shims/ContentService');
global.Logger = require('../shims/Logger');

// --- Mock UrlFetchApp для перехвата сообщений в Telegram ---
const sentMessages = [];
global.UrlFetchApp = {
  fetch: function(url, options) {
    sentMessages.push({ url: url, payload: options ? options.payload : null });
    return {
      getContentText: function() { return '{"ok":true}'; },
      getResponseCode: function() { return 200; }
    };
  }
};

// --- Подключаем бота ---
const bot = require('../src/bot');

// ==================== ХЕЛПЕРЫ ====================

const DATA_DIR = path.join(__dirname, '..', 'data');

function clearData() {
  ['Конфиг.csv', 'Ученики.csv', 'Транзакции.csv', 'properties.json'].forEach(f => {
    const p = path.join(DATA_DIR, f);
    if (fs.existsSync(p)) fs.unlinkSync(p);
  });
  sentMessages.length = 0;
  // Предзаполняем конфиг тестовым токеном
  fs.writeFileSync(path.join(DATA_DIR, 'Конфиг.csv'), 'Ключ,Значение\nBOT_TOKEN,test_token_12345\n', 'utf8');
}

function makeEvent(updateId, chatId, text, firstName, chatType) {
  return {
    postData: {
      contents: JSON.stringify({
        update_id: updateId,
        message: {
          message_id: 1,
          from: {
            id: parseInt(firstName === "Admin" ? 320246687 : 111222333),
            first_name: firstName || "TestUser",
            is_bot: false
          },
          chat: {
            id: parseInt(chatId),
            first_name: firstName || "TestUser",
            type: chatType || "private"
          },
          date: Math.floor(Date.now() / 1000),
          text: text
        }
      })
    }
  };
}

function readCsv(name) {
  const p = path.join(DATA_DIR, `${name}.csv`);
  if (!fs.existsSync(p)) return [];
  const lines = fs.readFileSync(p, 'utf8').trim().split('\n').filter(l => l.trim());
  if (lines.length === 0) return [];
  const { parse } = require('csv-parse/sync');
  return parse(lines.join('\n'), { columns: false, skip_empty_lines: true });
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

function assertIncludes(text, substring, msg) {
  if (!text.includes(substring)) {
    throw new Error((msg || `Expected "${text}" to include "${substring}"`));
  }
}

function findMessage(substring) {
  for (const m of sentMessages) {
    if (m.payload && m.payload.includes(substring)) return m;
  }
  return null;
}

function assertAnyMessageIncludes(substring, msg) {
  if (!findMessage(substring)) {
    throw new Error(msg || `Expected at least one sent message to include "${substring}"`);
  }
}

// ==================== КОНСТАНТЫ ====================

let TEST_ADMIN_ID = "320246687";
let TEST_STUDENT_PERSONAL_ID = "111222333";
let TEST_STUDENT_GROUP_ID = "-123456789";

// ==================== ТЕСТЫ ====================

async function test01_StartSetsAdmin() {
  clearData();
  const res = bot.doPost(makeEvent(1, TEST_ADMIN_ID, "/start", "Admin"));
  assert(res.getContent() === "OK", "Expected OK response");
  
  const cfg = readCsv('Конфиг');
  let adminRow = null;
  for (let i = 1; i < cfg.length; i++) {
    if (cfg[i][0] === "ADMIN_CHAT_ID") adminRow = cfg[i];
  }
  assert(adminRow !== null, "Expected ADMIN_CHAT_ID key");
  assert(adminRow[1] === TEST_ADMIN_ID, `Expected admin ${TEST_ADMIN_ID}, got ${adminRow[1]}`);
  assert(sentMessages.length >= 1, "Bot should send a message");
  assertAnyMessageIncludes("репетитором", "Should greet as tutor");
}

async function test02_AdminStartAgain() {
  const res = bot.doPost(makeEvent(2, TEST_ADMIN_ID, "/start", "Admin"));
  assert(res.getContent() === "OK", "Expected OK");
  assertAnyMessageIncludes("Вы уже админ", "Should say 'already admin'");
}

async function test03_MyIdPrivate() {
  const res = bot.doPost(makeEvent(3, TEST_ADMIN_ID, "/myid", "Admin"));
  assert(res.getContent() === "OK");
  assertAnyMessageIncludes(TEST_ADMIN_ID, "Should return personal chat_id");
}

async function test04_MyIdGroup() {
  const res = bot.doPost(makeEvent(4, TEST_STUDENT_GROUP_ID, "/myid", "Admin", "group"));
  assert(res.getContent() === "OK");
  assertAnyMessageIncludes(TEST_STUDENT_GROUP_ID, "Should return group chat_id");
  assertAnyMessageIncludes("Используйте его при добавлении", "Should hint admin");
}

async function test05_AddStudentWithGroup() {
  const res = bot.doPost(makeEvent(5, TEST_ADMIN_ID, `/addstudent ${TEST_STUDENT_PERSONAL_ID} ${TEST_STUDENT_GROUP_ID} Анна`, "Admin"));
  assert(res.getContent() === "OK");
  
  const students = readCsv('Ученики');
  assert(students.length >= 2, "Students should have data");
  const lastRow = students[students.length - 1];
  assert(lastRow[0] === TEST_STUDENT_PERSONAL_ID, "Personal chat_id should match");
  assert(lastRow[1] === "Анна", "Name should be Анна");
  assert(lastRow[6] === TEST_STUDENT_GROUP_ID, `Group chat_id should be ${TEST_STUDENT_GROUP_ID}, got ${lastRow[6]}`);
  
  assertAnyMessageIncludes("Анна", "Should confirm student added");
  assertAnyMessageIncludes(TEST_STUDENT_GROUP_ID, "Should mention group id");
}

async function test06_StatsShowsStudent() {
  const res = bot.doPost(makeEvent(6, TEST_ADMIN_ID, "/stats", "Admin"));
  assert(res.getContent() === "OK");
  assertAnyMessageIncludes("Анна", "Stats should include student name");
  assertAnyMessageIncludes("0 занятий", "Stats should show 0 lessons");
}

async function test07_StudentTopUpPrivate() {
  const res = bot.doPost(makeEvent(7, TEST_STUDENT_PERSONAL_ID, "+4", "Анна"));
  assert(res.getContent() === "OK");
  
  const students = readCsv('Ученики');
  const lastRow = students[students.length - 1];
  assert(parseInt(lastRow[2]) === 4, `Expected bought=4, got ${lastRow[2]}`);
  
  const trans = readCsv('Транзакции');
  const lastTrans = trans[trans.length - 1];
  assert(lastTrans[3] === "пополнение", "Expected пополнение");
  assert(parseInt(lastTrans[4]) === 4, "Expected count=4");
  
  assertAnyMessageIncludes("Пополнение", "Should confirm top-up");
}

async function test08_GroupTopUpIgnored() {
  // Пополнение в группе должно игнорироваться
  const before = sentMessages.length;
  const res = bot.doPost(makeEvent(8, TEST_STUDENT_GROUP_ID, "+4", "Анна", "group"));
  assert(res.getContent() === "OK", "Should return OK");
  // Не должно быть новых сообщений (мусор в группе игнорируется)
  assert(sentMessages.length === before, "Group top-up should be silently ignored");
}

async function test09_GroupMeetCharge() {
  // Репетитор кидает Meet в группу
  const res = bot.doPost(makeEvent(9, TEST_STUDENT_GROUP_ID, "meet.google.com/abc-defg-hij", "Admin", "group"));
  assert(res.getContent() === "OK");
  
  const students = readCsv('Ученики');
  const lastRow = students[students.length - 1];
  assert(parseInt(lastRow[3]) === 1, `Expected spent=1, got ${lastRow[3]}`);
  
  const trans = readCsv('Транзакции');
  const lastTrans = trans[trans.length - 1];
  assert(lastTrans[3] === "списание", "Expected списание");
  
  assertAnyMessageIncludes("Осталось", "Should show remaining");
}

async function test10_MultipleTopUpAndMeet() {
  // Еще +2 в личку
  bot.doPost(makeEvent(10, TEST_STUDENT_PERSONAL_ID, "пакет 2", "Анна"));
  // Еще одна ссылка в группу
  bot.doPost(makeEvent(11, TEST_STUDENT_GROUP_ID, "meet.google.com/xxx-yyy-zzz", "Admin", "group"));
  
  const students = readCsv('Ученики');
  const lastRow = students[students.length - 1];
  assert(parseInt(lastRow[2]) === 6, `Expected total bought=6, got ${lastRow[2]}`);
  assert(parseInt(lastRow[3]) === 2, `Expected total spent=2, got ${lastRow[3]}`);
}

async function test11_StatsAfterActivity() {
  bot.doPost(makeEvent(12, TEST_ADMIN_ID, "/stats", "Admin"));
  assertAnyMessageIncludes("Анна", "Stats should show Анна");
  assertAnyMessageIncludes("4 занятий", "Stats should show remaining 4 lessons (6-2)");
}

async function test12_UnregisteredUser() {
  const UNKNOWN_ID = "999888777";
  const res = bot.doPost(makeEvent(13, UNKNOWN_ID, "+5", "Unknown"));
  assert(res.getContent() === "OK");
  assertAnyMessageIncludes("не зарегистрированы", "Should reject unknown user");
}

async function test13_UnboundGroup() {
  // Группа без привязанного ученика
  const UNBOUND_GROUP = "-999999999";
  const res = bot.doPost(makeEvent(14, UNBOUND_GROUP, "meet.google.com/test", "Admin", "group"));
  assert(res.getContent() === "OK");
  assertAnyMessageIncludes("не привязана", "Should warn about unbound group");
}

async function test14_AdminUnknownCommand() {
  const res = bot.doPost(makeEvent(15, TEST_ADMIN_ID, "какая-то ерунда", "Admin"));
  assert(res.getContent() === "OK");
  assertAnyMessageIncludes("админ", "Should remind admin commands");
}

async function test15_ZeroBalanceBlock() {
  clearData();
  bot.clearDuplicateProtection();
  
  bot.doPost(makeEvent(100, TEST_ADMIN_ID, "/start", "Admin"));
  bot.doPost(makeEvent(101, TEST_ADMIN_ID, `/addstudent ${TEST_STUDENT_PERSONAL_ID} ${TEST_STUDENT_GROUP_ID} БедныйУченик`, "Admin"));
  // Баланс 0, пытаемся списать в группе
  bot.doPost(makeEvent(102, TEST_STUDENT_GROUP_ID, "meet.google.com/zero-balance-test", "Admin", "group"));
  
  assertAnyMessageIncludes("закончились", "Should warn about zero balance");
  
  const trans = readCsv('Транзакции');
  assert(trans.length <= 1, "Should not create transaction on zero balance");
}

async function test16_DuplicateProtection() {
  clearData();
  bot.clearDuplicateProtection();
  
  bot.doPost(makeEvent(200, TEST_ADMIN_ID, "/start", "Admin"));
  const msgCountBefore = sentMessages.length;
  
  bot.doPost(makeEvent(200, TEST_ADMIN_ID, "/start", "Admin"));
  const msgCountAfter = sentMessages.length;
  
  assert(msgCountBefore === msgCountAfter, "Duplicate should be ignored, no new messages");
}

async function test17_SetBotToken() {
  clearData();
  process.env.BOT_TOKEN = "TEST_TOKEN_12345";
  bot.setBotToken();
  
  const cfg = readCsv('Конфиг');
  assert(cfg.length >= 2, "Config should have data");
  assert(cfg[1][0] === "BOT_TOKEN", "Expected BOT_TOKEN key");
  assert(cfg[1][1] === "TEST_TOKEN_12345", "Expected token to be saved");
  delete process.env.BOT_TOKEN;
}

async function test18_OneLessonWarning() {
  clearData();
  bot.clearDuplicateProtection();
  
  bot.doPost(makeEvent(300, TEST_ADMIN_ID, "/start", "Admin"));
  bot.doPost(makeEvent(301, TEST_ADMIN_ID, `/addstudent ${TEST_STUDENT_PERSONAL_ID} ${TEST_STUDENT_GROUP_ID} Предупреждаемый`, "Admin"));
  // Пополняем на 2 в личку
  bot.doPost(makeEvent(302, TEST_STUDENT_PERSONAL_ID, "+2", "Предупреждаемый"));
  // Списываем 1 в группе -> баланс станет 1
  bot.doPost(makeEvent(303, TEST_STUDENT_GROUP_ID, "meet.google.com/one-left-test", "Admin", "group"));
  
  assertAnyMessageIncludes("⚠️ У вас осталось", "Should warn student about 1 lesson remaining");
  assertAnyMessageIncludes("🔔 У ученика", "Should warn admin about 1 lesson remaining");
}

async function test19_AddStudentWithoutGroup() {
  clearData();
  bot.clearDuplicateProtection();
  
  bot.doPost(makeEvent(400, TEST_ADMIN_ID, "/start", "Admin"));
  const res = bot.doPost(makeEvent(401, TEST_ADMIN_ID, `/addstudent ${TEST_STUDENT_PERSONAL_ID} БезГруппы`, "Admin"));
  assert(res.getContent() === "OK");
  
  const students = readCsv('Ученики');
  const lastRow = students[students.length - 1];
  assert(lastRow[0] === TEST_STUDENT_PERSONAL_ID, "Personal chat_id should match");
  assert(lastRow[1] === "БезГруппы", "Name should match");
  assert(lastRow[6] === "", "Group chat_id should be empty");
  assertAnyMessageIncludes("БезГруппы", "Should confirm student added");
}

// ==================== РАННЕР ====================

const tests = [
  { name: "/start назначает админа", fn: test01_StartSetsAdmin },
  { name: "Повторный /start у админа", fn: test02_AdminStartAgain },
  { name: "/myid в личке возвращает chat_id", fn: test03_MyIdPrivate },
  { name: "/myid в группе возвращает ID группы", fn: test04_MyIdGroup },
  { name: "/addstudent с group_chat_id", fn: test05_AddStudentWithGroup },
  { name: "/stats показывает ученика", fn: test06_StatsShowsStudent },
  { name: "Пополнение в личке работает", fn: test07_StudentTopUpPrivate },
  { name: "Пополнение в группе игнорируется", fn: test08_GroupTopUpIgnored },
  { name: "Meet в группе списывает занятие", fn: test09_GroupMeetCharge },
  { name: "Несколько пополнений и списаний", fn: test10_MultipleTopUpAndMeet },
  { name: "/stats после активности", fn: test11_StatsAfterActivity },
  { name: "Незарегистрированный пользователь отклонен", fn: test12_UnregisteredUser },
  { name: "Непривязанная группа — предупреждение", fn: test13_UnboundGroup },
  { name: "Админ получает подсказку на мусор", fn: test14_AdminUnknownCommand },
  { name: "При нулевом балансе списание блокируется", fn: test15_ZeroBalanceBlock },
  { name: "Защита от дубликатов работает", fn: test16_DuplicateProtection },
  { name: "setBotToken сохраняет токен", fn: test17_SetBotToken },
  { name: "Уведомление при 1 оставшемся занятии", fn: test18_OneLessonWarning },
  { name: "/addstudent без group_chat_id", fn: test19_AddStudentWithoutGroup },
];

async function runAll() {
  console.log("============================================");
  console.log("🧪 ЗАПУСК ПОЛНОГО НАБОРА ТЕСТОВ");
  console.log("============================================\n");
  
  let passed = 0;
  let failed = 0;
  
  for (const test of tests) {
    try {
      await test.fn();
      console.log(`  ✅ ${test.name}`);
      passed++;
    } catch (err) {
      console.log(`  ❌ ${test.name}`);
      console.log(`     ${err.message}`);
      failed++;
    }
  }
  
  console.log("\n============================================");
  console.log(`📊 РЕЗУЛЬТАТ: ${passed} пройдено, ${failed} не пройдено из ${tests.length}`);
  console.log("============================================");
  
  process.exit(failed > 0 ? 1 : 0);
}

runAll().catch(err => {
  console.error("Критическая ошибка тест-раннера:", err);
  process.exit(1);
});
