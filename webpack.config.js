const path = require('path');
const WebpackFluentPlugin = require('./l10n/WebpackFluentPlugin.js');

module.exports = {
  entry: {
    index: './tsundoku/blueprints/ux/static/ts/index/app.tsx',
    nyaa: './tsundoku/blueprints/ux/static/ts/nyaa/app.tsx',
    webhooks: './tsundoku/blueprints/ux/static/ts/webhooks/app.tsx',
    config: './tsundoku/blueprints/ux/static/ts/config/app.tsx',
    logs: './tsundoku/blueprints/ux/static/ts/logs/app.tsx'
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
      'react': 'preact/compat',
      'react-dom': 'preact/compat',
      '~': path.resolve('./node_modules')
    },
    fallback: {
      buffer: false
    }
  },
  plugins: [new WebpackFluentPlugin()],
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'tsundoku/blueprints/ux/static/js/'),
  }
};
