const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');
const { stringify } = require('csv-stringify/sync');

const DATA_DIR = path.join(__dirname, '..', 'data');

function getCsvPath(name) {
  return path.join(DATA_DIR, `${name}.csv`);
}

function readCsv(name) {
  const filePath = getCsvPath(name);
  if (!fs.existsSync(filePath)) return [];
  const content = fs.readFileSync(filePath, 'utf8');
  if (!content.trim()) return [];
  return parse(content, { columns: false, skip_empty_lines: true });
}

function writeCsv(name, rows) {
  const filePath = getCsvPath(name);
  const content = stringify(rows);
  fs.writeFileSync(filePath, content, 'utf8');
}

class Range {
  constructor(sheet, row, col, rows, cols) {
    this._sheet = sheet;
    this._row = row;
    this._col = col;
    this._rows = rows || 1;
    this._cols = cols || 1;
  }

  getValue() {
    const data = this._sheet._getData();
    const r = this._row - 1;
    const c = this._col - 1;
    if (r < 0 || r >= data.length || c < 0 || c >= data[r].length) return '';
    return data[r][c];
  }

  setValue(value) {
    const data = this._sheet._getData();
    const r = this._row - 1;
    const c = this._col - 1;
    while (data.length <= r) data.push([]);
    while (data[r].length <= c) data[r].push('');
    data[r][c] = value;
    this._sheet._setData(data);
    return this;
  }

  setValues(values) {
    const data = this._sheet._getData();
    for (let i = 0; i < values.length; i++) {
      const r = this._row - 1 + i;
      while (data.length <= r) data.push([]);
      for (let j = 0; j < values[i].length; j++) {
        const c = this._col - 1 + j;
        while (data[r].length <= c) data[r].push('');
        data[r][c] = values[i][j];
      }
    }
    this._sheet._setData(data);
    return this;
  }

  setFormula(formula) {
    this.setValue(formula);
    return this;
  }

  setFontWeight(weight) {
    // no-op for local simulation
  }
}

class DataRange {
  constructor(sheet) {
    this._sheet = sheet;
  }
  getValues() {
    return this._sheet._getData();
  }
}

class Sheet {
  constructor(name, headers) {
    this._name = name;
    this._headers = headers;
    if (!fs.existsSync(getCsvPath(name)) && headers) {
      writeCsv(name, [headers]);
    }
  }

  _getData() {
    return readCsv(this._name);
  }

  _setData(data) {
    writeCsv(this._name, data);
  }

  getDataRange() {
    return new DataRange(this);
  }

  getRange(row, col, rows, cols) {
    return new Range(this, row, col, rows, cols);
  }

  appendRow(row) {
    const data = this._getData();
    data.push(row.map(v => v === undefined || v === null ? '' : String(v)));
    this._setData(data);
  }

  getLastRow() {
    return this._getData().length;
  }

  getSheetByName() {
    return null;
  }
}

class Spreadsheet {
  getSheetByName(name) {
    const filePath = getCsvPath(name);
    if (!fs.existsSync(filePath)) return null;
    return new Sheet(name);
  }

  insertSheet(name) {
    return new Sheet(name);
  }
}

class SpreadsheetAppShim {
  getActiveSpreadsheet() {
    return new Spreadsheet();
  }
}

module.exports = new SpreadsheetAppShim();
