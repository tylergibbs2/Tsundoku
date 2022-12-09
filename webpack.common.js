const path = require("path");
const WebpackFluentPlugin = require("./l10n/WebpackFluentPlugin.js");

module.exports = {
  entry: {
    root: "./tsundoku/blueprints/ux/static/ts/App.tsx",
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: ["ts-loader"],
        exclude: /node_modules/,
      },
      {
        test: /\.s?[ac]ss$/i,
        use: ["style-loader", "css-loader", "sass-loader"],
      },
      {
        test: /\.js/,
        include: /@fluent[\\/](bundle|langneg|syntax)[\\/]/,
        type: "javascript/auto",
      },
    ],
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js"],
    alias: {
      "~": path.resolve("./node_modules"),
    },
    fallback: {
      buffer: false,
    },
  },
  plugins: [new WebpackFluentPlugin()],
};
