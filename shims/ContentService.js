class TextOutput {
  constructor(text) {
    this._text = text;
  }
  getContent() {
    return this._text;
  }
}

class ContentServiceShim {
  createTextOutput(text) {
    return new TextOutput(text);
  }
}

module.exports = new ContentServiceShim();
