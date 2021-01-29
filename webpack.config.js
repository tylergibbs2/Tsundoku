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
        use: ['ts-loader'],
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    alias: {
      'react': 'preact/compat',
      'react-dom': 'preact/compat',
      '~': path.resolve('./node_modules')
    }
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'tsundoku/blueprints/ux/static/js/'),
  }
};