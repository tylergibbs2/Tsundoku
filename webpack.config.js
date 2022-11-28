const path = require('path');
const WebpackFluentPlugin = require('./l10n/WebpackFluentPlugin.js');

module.exports = {
  entry: {
    root: './tsundoku/blueprints/ux/static/ts/App.tsx',
    webhooks: './tsundoku/blueprints/ux/static/ts/PageWebhooks/App.tsx',
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: ['ts-loader'],
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      },
      {
        test: /\.js/,
        include: /@fluent[\\/](bundle|langneg|syntax)[\\/]/,
        type: "javascript/auto",
      }
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    alias: {
      '~': path.resolve('./node_modules')
    },
    fallback: {
      buffer: false
    }
  },
  plugins: [new WebpackFluentPlugin()],
  output: {
    filename: '[name].js',
    sourceMapFilename: '[name].js.map',
    path: path.resolve(__dirname, 'tsundoku/blueprints/ux/static/js/'),
  },
  devtool: "source-map"
};
