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
        use: [
          "style-loader",
          "css-loader",
          {
            loader: "sass-loader",
            options: {
              // NOTE: we stay on the legacy Sass JS API on purpose. The modern
              // API changes import resolution so bare `@import "bulma"` (a
              // node_modules package) no longer resolves. Silence the noisy
              // deprecations instead; migrating fully is blocked on bulma 1.x.
              sassOptions: {
                silenceDeprecations: [
                  // We are knowingly using the legacy API (see note above).
                  "legacy-js-api",
                  // Our stylesheets + bulma 0.9.x still use `@import`.
                  "import",
                ],
                // Silence deprecation warnings originating in dependencies
                // (bulma 0.9.x internals: darken(), red(), etc.).
                quietDeps: true,
              },
            },
          },
        ],
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
  output: {
    path: path.resolve(__dirname, "tsundoku/blueprints/ux/static/js/"),
    clean: true,
  },
};
