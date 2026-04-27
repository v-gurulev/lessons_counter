const fs = require('fs');
const path = require('path');

const propsPath = path.join(__dirname, '..', 'data', 'properties.json');

function readProps() {
  try {
    return JSON.parse(fs.readFileSync(propsPath, 'utf8'));
  } catch {
    return {};
  }
}

function writeProps(data) {
  fs.writeFileSync(propsPath, JSON.stringify(data, null, 2), 'utf8');
}

class ScriptProperties {
  getProperty(key) {
    const data = readProps();
    return data[key] || null;
  }
  setProperty(key, value) {
    const data = readProps();
    data[key] = value;
    writeProps(data);
  }
  deleteProperty(key) {
    const data = readProps();
    delete data[key];
    writeProps(data);
  }
}

class PropertiesServiceShim {
  getScriptProperties() {
    return new ScriptProperties();
  }
}

module.exports = new PropertiesServiceShim();
