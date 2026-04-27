class SessionShim {
  getScriptTimeZone() {
    return 'Europe/Moscow';
  }
}

module.exports = new SessionShim();
