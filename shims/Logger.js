class LoggerShim {
  log(message) {
    console.log(`[LOG] ${message}`);
  }
}

module.exports = new LoggerShim();
