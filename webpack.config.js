const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");

module.exports = {
  entry: "./src/index.js",
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "bundle.[contenthash].js",
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env", "@babel/preset-react"],
          },
        },
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
    ],
  },
  resolve: {
    extensions: [".js", ".jsx"],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./public/index.html",
      favicon: false,
    }),
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, "__cursor_data"),
      publicPath: "/__cursor_data",
      watch: false, // Disable watching for static files
    },
    port: 3001,
    hot: true,
    open: true,
  },
  watchOptions: {
    ignored: ["**/node_modules", "**/__cursor_data/**/*.png"],
  },
};
