class UtilitiesShim {
  formatDate(date, timeZone, format) {
    const d = new Date(date);
    const options = {
      timeZone: timeZone || 'Europe/Moscow',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    };
    const parts = new Intl.DateTimeFormat('ru-RU', options).formatToParts(d);
    const getPart = (type) => parts.find(p => p.type === type)?.value;
    
    if (format === 'dd.MM.yyyy HH:mm') {
      return `${getPart('day')}.${getPart('month')}.${getPart('year')} ${getPart('hour')}:${getPart('minute')}`;
    }
    return d.toLocaleString('ru-RU', options);
  }
}

module.exports = new UtilitiesShim();
