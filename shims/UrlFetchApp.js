class HTTPResponse {
  constructor(res, body) {
    this._res = res;
    this._body = body;
  }
  getContentText() {
    return this._body;
  }
  getResponseCode() {
    return this._res.status;
  }
}

class UrlFetchAppShim {
  async fetch(url, options) {
    const fetchOptions = {
      method: options?.method || 'GET',
      headers: options?.headers || {}
    };
    if (options?.payload) {
      fetchOptions.body = options.payload;
    }
    if (options?.contentType) {
      fetchOptions.headers['Content-Type'] = options.contentType;
    }
    
    const res = await fetch(url, fetchOptions);
    const body = await res.text();
    return new HTTPResponse({ status: res.status }, body);
  }
}

module.exports = new UrlFetchAppShim();
