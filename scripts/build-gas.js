/**
 * Скрипт сборки: превращает локальный src/bot.js в готовый код для Google Apps Script
 * Запуск: npm run build:gas
 * Выход: dist/bot.gas.js — скопируйте содержимое в редактор GAS целиком
 */

const fs = require('fs');
const path = require('path');

const srcPath = path.join(__dirname, '..', 'src', 'bot.js');
const distPath = path.join(__dirname, '..', 'dist', 'bot.gas.js');

let code = fs.readFileSync(srcPath, 'utf8');

// 1. В findStudent: возвращаем чтение баланса из ячейки (как в оригинале GAS)
code = code.replace(
  /balance: bought - spent, \/\/ В локальной версии считаем динамически/,
  'balance: Number(data[i][4]) || 0,'
);

// 2. В addStudent: возвращаем формулу для баланса (как в оригинале GAS)
code = code.replace(
  /function addStudent\(sheet, chatId, name\) \{\n  sheet\.appendRow\(\[chatId, name, 0, 0, "0", ""\]\);\n  \/\/ Баланс считается динамически в findStudent\n\}/,
  'function addStudent(sheet, chatId, name) {\n  sheet.appendRow([chatId, name, 0, 0, "", ""]);\n  var lastRow = sheet.getLastRow();\n  sheet.getRange(lastRow, 5).setFormula("=C" + lastRow + "-D" + lastRow);\n}'
);

// 3. В getStats: читаем баланс из колонки E вместо вычисления
code = code.replace(
  /var bought = Number\(data\[i\]\[2\]\) \|\| 0;\n    var spent = Number\(data\[i\]\[3\]\) \|\| 0;\n    var bal = bought - spent;/,
  'var bal = Number(data[i][4]) || 0;'
);

// 4. В logTransaction: возвращаем new Date() вместо toISOString (GAS сам форматирует)
code = code.replace(
  /sheet\.appendRow\(\[new Date\(\)\.toISOString\(\), chatId, name, type, count, note\]\);/,
  'sheet.appendRow([new Date(), chatId, name, type, count, note]);'
);

// 5. В setBotToken: убираем проверку process.env, оставляем только строку для GAS
code = code.replace(
  /var TOKEN = \(typeof process !== "undefined" && process\.env && process\.env\.BOT_TOKEN\) \? process\.env\.BOT_TOKEN : "ВАШ_ТОКЕН_ЗДЕСЬ";/,
  'var TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"; // <--- ЗАМЕНИТЕ ЭТО'
);

// 6. Удаляем блок EXPORTS в конце
const exportMarker = '// ==================== EXPORTS (только для Node.js) ====================';
const exportIdx = code.indexOf(exportMarker);
if (exportIdx !== -1) {
  code = code.substring(0, exportIdx).trimEnd() + '\n';
}

fs.writeFileSync(distPath, code, 'utf8');

console.log('✅ Сборка завершена: ' + distPath);
console.log('');
console.log('Следующие изменения применены для GAS:');
console.log('  • Баланс читается из ячейки (формула =C-D)');
console.log('  • addStudent создает формулу в колонке E');
console.log('  • Дата транзакции передается как объект Date');
console.log('  • Убраны Node.js-экспорты');
console.log('');
console.log('Дальше: скопируйте содержимое dist/bot.gas.js в редактор Apps Script');
