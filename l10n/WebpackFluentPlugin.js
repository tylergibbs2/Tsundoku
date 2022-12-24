const fs = require("fs");
const path = require("path");

const { DefinePlugin } = require("webpack");

module.exports = class WebpackTranslationsPlugin {
  constructor({ directory = "l10n" } = {}) {
    this.directory = directory;
  }

  apply(compiler) {
    this.setPath(compiler.context);

    new DefinePlugin({
      "window.TRANSLATIONS": JSON.stringify(this.getTranslations()),
    }).apply(compiler);
  }

  setPath(context) {
    this.path = path.resolve(context, this.directory);
  }

  getTranslations() {
    let paths = getTranslationFiles(this.path);
    let translations = {};

    for (const fp of paths) {
      let data = read(fp);

      let relative = path.relative(__dirname, fp);
      let parts = relative.split(path.sep);
      let key = parts.join("/");
      translations[key] = data;
    }

    return translations;
  }
};

function getTranslationFiles(dir) {
  let files = [];

  const cb = (file, stats) => {
    if (path.extname(file) === ".ftl") files.push(file);
  };

  walk(dir, cb);
  return files;
}

function walk(dir, callback) {
  const files = fs.readdirSync(dir);
  files.forEach((file) => {
    let fp = path.join(dir, file);
    const stats = fs.statSync(fp);
    if (stats.isDirectory()) walk(fp, callback);
    else callback(fp, stats);
  });
}

function read(path) {
  return fs.readFileSync(path, "utf-8");
}
