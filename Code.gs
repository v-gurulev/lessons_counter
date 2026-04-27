// ==================== НАСТРОЙКИ ====================
var SHEET_NAME_STUDENTS = "Ученики";
var SHEET_NAME_TRANSACTIONS = "Транзакции";
var SHEET_NAME_CONFIG = "Конфиг";

function doGet(e) {
  return ContentService.createTextOutput("Bot is running");
}

// ==================== WEBHOOK (главная точка входа) ====================
function doPost(e) {
  try {
    var update = JSON.parse(e.postData.contents);
    if (!update.message) return ContentService.createTextOutput("OK");

    // --- Защита от дубликатов Telegram ---
    var updateId = update.update_id;
    var props = PropertiesService.getScriptProperties();
    var lastId = props.getProperty("last_update_id");
    if (lastId && parseInt(lastId) >= updateId) {
      Logger.log("Пропуск дубликата: update_id=" + updateId + ", lastId=" + lastId);
      return ContentService.createTextOutput("OK");
    }
    props.setProperty("last_update_id", updateId.toString());

    var msg = update.message;
    var chatId = msg.chat.id.toString();
    var text = msg.text || "";
    var userName = msg.from.first_name || "Unknown";
    var chatType = msg.chat.type || "private";
    var isGroup = (chatType === "group" || chatType === "supergroup");

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var configSheet = getOrCreateSheet(ss, SHEET_NAME_CONFIG, ["Ключ", "Значение"]);
    var studentsSheet = getOrCreateSheet(ss, SHEET_NAME_STUDENTS, ["chat_id", "Имя", "Всего куплено", "Всего проведено", "Баланс", "Дата последнего занятия", "group_chat_id"]);
    var transSheet = getOrCreateSheet(ss, SHEET_NAME_TRANSACTIONS, ["Дата", "chat_id", "Имя", "Тип", "Количество", "Описание"]);

    var adminId = getConfig(configSheet, "ADMIN_CHAT_ID");

    // --- Первый запуск: назначаем админа (только в личке) ---
    if (!adminId && !isGroup && text === "/start") {
      setConfig(configSheet, "ADMIN_CHAT_ID", chatId);
      sendMessage(chatId, "👨‍🏫 Вы назначены репетитором (админом).\n\nКоманды:\n/addstudent [chat_id] [group_chat_id] [Имя] — добавить ученика\n/stats — сводка по всем ученикам\n/myid — узнать свой chat_id или ID группы\n\nЧтобы протестировать, добавьте себя как ученика:\n/addstudent " + chatId + " ТестовыйУченик");
      return ContentService.createTextOutput("OK");
    }

    if (!adminId) {
      if (!isGroup) sendMessage(chatId, "Напишите /start для первоначальной настройки.");
      return ContentService.createTextOutput("OK");
    }

    // --- /start для уже назначенного админа (только в личке) ---
    if (!isGroup && text === "/start" && chatId === adminId) {
      sendMessage(chatId, "👨‍🏫 Вы уже админ.\n\nКоманды:\n• /addstudent [chat_id] [group_chat_id] [Имя]\n• /stats\n• /myid\n\nЧтобы протестировать как ученик, добавьте себя:\n/addstudent " + chatId + " Тест");
      return ContentService.createTextOutput("OK");
    }

    // --- Команда /addstudent (только админ, только в личке) ---
    if (!isGroup && text.startsWith("/addstudent") && chatId === adminId) {
      var parts = text.split(" ");
      if (parts.length >= 3) {
        var newChatId = parts[1];
        var groupChatId = null;
        var nameStartIdx = 2;

        // Если третий аргумент начинается с '-', считаем его group_chat_id
        if (parts.length >= 4 && parts[2].startsWith("-")) {
          groupChatId = parts[2];
          nameStartIdx = 3;
        }

        if (nameStartIdx < parts.length) {
          var newName = parts.slice(nameStartIdx).join(" ");
          addStudent(studentsSheet, newChatId, newName, groupChatId);
          var confirm = "✅ Ученик добавлен: *" + newName + "* (личный ID: `" + newChatId + "`";
          if (groupChatId) {
            confirm += ", группа: `" + groupChatId + "`";
          }
          confirm += ")";
          sendMessage(chatId, confirm, "Markdown");
        } else {
          sendMessage(chatId, "❌ Формат: `/addstudent [chat_id] [group_chat_id] [Имя]`\n`group_chat_id` опционально (начинается с `-`)\nСвой chat_id можно узнать через /myid", "Markdown");
        }
      } else {
        sendMessage(chatId, "❌ Формат: `/addstudent [chat_id] [group_chat_id] [Имя]`\n`group_chat_id` опционально (начинается с `-`)\nСвой chat_id можно узнать через /myid", "Markdown");
      }
      return ContentService.createTextOutput("OK");
    }

    // --- Команда /stats (только админ, только в личке) ---
    if (!isGroup && text === "/stats" && chatId === adminId) {
      sendMessage(chatId, getStats(studentsSheet), "Markdown");
      return ContentService.createTextOutput("OK");
    }

    // --- Команда /myid (для всех, везде) ---
    if (text === "/myid") {
      if (isGroup) {
        sendMessage(chatId, "ID этой группы: `" + chatId + "`\n\nИспользуйте его при добавлении ученика:\n`/addstudent [личный_chat_id] " + chatId + " [Имя]`", "Markdown");
      } else {
        sendMessage(chatId, "Ваш chat_id: `" + chatId + "`", "Markdown");
      }
      return ContentService.createTextOutput("OK");
    }

    // --- Ищем ученика ---
    var student = null;
    if (isGroup) {
      // В группе ищем по group_chat_id (колонка G)
      student = findStudent(studentsSheet, null, chatId);
    } else {
      // В личке ищем по личному chat_id (колонка A)
      student = findStudent(studentsSheet, chatId, null);
    }

    // --- Группа: если не привязана к ученику ---
    if (isGroup && !student) {
      if (text.includes("meet.google.com") || text.startsWith("/")) {
        sendMessage(chatId, "⛔ Эта группа не привязана к ученику. Админ: используйте `/addstudent [личный_chat_id] " + chatId + " [Имя]`", "Markdown");
      }
      return ContentService.createTextOutput("OK");
    }

    // --- Личка: не ученик и не админ ---
    if (!isGroup && !student && chatId !== adminId) {
      sendMessage(chatId, "⛔ Вы не зарегистрированы. Попросите репетитора добавить вас.");
      return ContentService.createTextOutput("OK");
    }

    // --- Личка: админ пишет что-то неизвестное (и он не ученик) ---
    if (!isGroup && !student && chatId === adminId) {
      sendMessage(chatId, "ℹ️ Вы админ.\nКоманды: /addstudent, /stats, /myid\n\nЧтобы протестировать как ученик, добавьте себя:\n`/addstudent " + chatId + " Тест`", "Markdown");
      return ContentService.createTextOutput("OK");
    }

    // ==================== СПИСАНИЕ: ссылка на Google Meet ====================
    // Работает в группе (основной сценарий) и в личке (для совместимости)
    if (text.includes("meet.google.com")) {
      if (!student) {
        sendMessage(chatId, "⛔ Вы не зарегистрированы.");
        return ContentService.createTextOutput("OK");
      }
      if (student.balance <= 0) {
        sendMessage(chatId, "⚠️ У вас закончились занятия! Пополните баланс.");
        sendMessage(adminId, "🚨 У ученика *" + student.name + "* баланс = 0!", "Markdown");
        return ContentService.createTextOutput("OK");
      }

      logTransaction(transSheet, student.chatId, student.name, "списание", 1, text);
      updateStudentCounter(studentsSheet, student.chatId, "spent", 1);
      updateStudentDate(studentsSheet, student.chatId);

      var newBal = student.balance - 1;
      sendMessage(chatId, "✅ Урок начался и засчитан.\nОсталось занятий: *" + newBal + "*", "Markdown");
      sendMessage(adminId, "📊 Ученик *" + student.name + "* — проведен урок.\nОсталось: *" + newBal + "*", "Markdown");

      if (newBal === 1) {
        sendMessage(chatId, "⚠️ У вас осталось *1* занятие. Не забудьте пополнить баланс!", "Markdown");
        sendMessage(adminId, "🔔 У ученика *" + student.name + "* осталось *1* занятие.", "Markdown");
      }

      return ContentService.createTextOutput("OK");
    }

    // ==================== ПОПОЛНЕНИЕ: ищем число ====================
    // Работает только в личке (в группе — игнорируем, чтобы не спамить)
    var numMatch = text.match(/(?:^|\s)\+?(\d+)(?:\s|$)/);
    if (numMatch && !isGroup) {
      var count = parseInt(numMatch[1]);
      if (count > 0 && count <= 50) {
        if (!student) {
          sendMessage(chatId, "⛔ Вы не зарегистрированы.");
          return ContentService.createTextOutput("OK");
        }
        logTransaction(transSheet, student.chatId, student.name, "пополнение", count, text);
        updateStudentCounter(studentsSheet, student.chatId, "bought", count);

        var newBal = student.balance + count;
        sendMessage(chatId, "💰 Пополнение на *" + count + "* занятий.\nТекущий баланс: *" + newBal + "*", "Markdown");
        sendMessage(adminId, "💰 Ученик *" + student.name + "* пополнил баланс на *" + count + "*.\nВсего: *" + newBal + "*", "Markdown");
        return ContentService.createTextOutput("OK");
      }
    }

    // --- В группе не отвечаем на мусор ---
    if (isGroup) {
      return ContentService.createTextOutput("OK");
    }

    // Ничего не подошло
    sendMessage(chatId, "🤔 Не понял команду.\n\nОтправьте число для пополнения (например: *+4* или *пакет 4*).\nРепетитор кидает ссылку на *Google Meet* — бот автоматически спишет занятие.", "Markdown");
    return ContentService.createTextOutput("OK");

  } catch (err) {
    Logger.log("ERROR: " + err + "\n" + err.stack);
    return ContentService.createTextOutput("Error");
  }
}

// ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

function getOrCreateSheet(ss, name, headers) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    if (headers) sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");
  }
  return sheet;
}

function getConfig(sheet, key) {
  var data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] === key) return data[i][1].toString();
  }
  return null;
}

function setConfig(sheet, key, value) {
  var data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] === key) {
      sheet.getRange(i + 1, 2).setValue(value);
      return;
    }
  }
  sheet.appendRow([key, value]);
}

function findStudent(sheet, chatId, groupChatId) {
  var data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    var matches = false;
    if (chatId && data[i][0].toString() === chatId.toString()) {
      matches = true;
    } else if (groupChatId && data[i][6] && data[i][6].toString() === groupChatId.toString()) {
      matches = true;
    }
    if (matches) {
      var bought = Number(data[i][2]) || 0;
      var spent = Number(data[i][3]) || 0;
      return {
        row: i + 1,
        chatId: data[i][0],
        name: data[i][1],
        bought: bought,
        spent: spent,
        balance: bought - spent,
        lastDate: data[i][5],
        groupChatId: data[i][6] || ""
      };
    }
  }
  return null;
}

function addStudent(sheet, chatId, name, groupChatId) {
  sheet.appendRow([chatId, name, 0, 0, "0", "", groupChatId || ""]);
  var lastRow = sheet.getLastRow();
  sheet.getRange(lastRow, 5).setFormula("=C" + lastRow + "-D" + lastRow);
}

function updateStudentCounter(sheet, chatId, field, delta) {
  var student = findStudent(sheet, chatId, null);
  if (!student) return;
  var col = (field === "bought") ? 3 : 4;
  var current = Number(sheet.getRange(student.row, col).getValue()) || 0;
  sheet.getRange(student.row, col).setValue(current + delta);
}

function updateStudentDate(sheet, chatId) {
  var student = findStudent(sheet, chatId, null);
  if (!student) return;
  var now = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd.MM.yyyy HH:mm");
  sheet.getRange(student.row, 6).setValue(now);
}

function logTransaction(sheet, chatId, name, type, count, note) {
  sheet.appendRow([new Date(), chatId, name, type, count, note]);
}

function getStats(sheet) {
  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return "📊 Учеников пока нет.";
  var msg = "📊 *Сводка по ученикам:*\n\n";
  for (var i = 1; i < data.length; i++) {
    var name = data[i][1] || "—";
    var bal = Number(data[i][4]) || 0;
    var last = data[i][5] || "—";
    msg += "• *" + name + "*: " + bal + " занятий _(последнее: " + last + ")_\n";
  }
  return msg;
}

function sendMessage(chatId, text, parseMode) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var configSheet = ss.getSheetByName(SHEET_NAME_CONFIG);
  var token = getConfig(configSheet, "BOT_TOKEN");
  if (!token) return;

  var url = "https://api.telegram.org/bot" + token + "/sendMessage";
  var payload = {
    chat_id: chatId,
    text: text,
    parse_mode: parseMode || "HTML"
  };
  UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
}

// ==================== РАЗОВАЯ УСТАНОВКА ====================
function setBotToken() {
  var TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"; // <--- ЗАМЕНИТЕ ЭТО
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var config = getOrCreateSheet(ss, SHEET_NAME_CONFIG, ["Ключ", "Значение"]);
  setConfig(config, "BOT_TOKEN", TOKEN);
  Logger.log("Токен сохранен в лист Конфиг");
}

function clearDuplicateProtection() {
  PropertiesService.getScriptProperties().deleteProperty("last_update_id");
  Logger.log("Защита от дублей очищена");
}
