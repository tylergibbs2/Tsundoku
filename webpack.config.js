const path = require('path');

module.exports = {
  entry: {
    login: './tsundoku/blueprints/ux/static/ts/login.tsx',
    index: './tsundoku/blueprints/ux/static/ts/index.tsx',
    nyaa_search: './tsundoku/blueprints/ux/static/ts/nyaa_search.tsx',
    webhooks: './tsundoku/blueprints/ux/static/ts/webhooks.tsx'
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'tsundoku/blueprints/ux/static/js/'),
  }
};