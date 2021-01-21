const path = require('path');

module.exports = {
  entry: {
    login: './tsundoku/blueprints/ux/static/ts/login/app.tsx',
    index: './tsundoku/blueprints/ux/static/ts/index/app.tsx',
    nyaa: './tsundoku/blueprints/ux/static/ts/nyaa/app.tsx',
    webhooks: './tsundoku/blueprints/ux/static/ts/webhooks/app.tsx'
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
    alias: {
      'react': 'preact/compat',
      'react-dom': 'preact/compat'
    }
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'tsundoku/blueprints/ux/static/js/'),
  }
};