const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const fs = require("fs");

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
    setupMiddlewares: (middlewares, devServer) => {
      // Add API endpoint to list available tags
      devServer.app.get("/api/tags", (req, res) => {
        const cursorDataDir = path.join(__dirname, "__cursor_data");

        if (!fs.existsSync(cursorDataDir)) {
          return res.json({ tags: [] });
        }

        try {
          const files = fs.readdirSync(cursorDataDir);

          // Extract tags from video files (screen_capture_<tag>.webm)
          const tags = files
            .filter(
              (file) =>
                file.startsWith("screen_capture_") && file.endsWith(".webm")
            )
            .map((file) => {
              // Remove "screen_capture_" prefix and ".webm" suffix
              return file.slice(15, -5);
            })
            .sort((a, b) => {
              // Sort by modification time, newest first
              const aPath = path.join(
                cursorDataDir,
                `screen_capture_${a}.webm`
              );
              const bPath = path.join(
                cursorDataDir,
                `screen_capture_${b}.webm`
              );
              const aStat = fs.statSync(aPath);
              const bStat = fs.statSync(bPath);
              return bStat.mtime - aStat.mtime;
            });

          res.json({ tags });
        } catch (error) {
          console.error("Error reading tags:", error);
          res.status(500).json({ error: "Failed to read tags" });
        }
      });

      return middlewares;
    },
  },
  watchOptions: {
    ignored: ["**/node_modules", "**/__cursor_data/**/*.png"],
  },
};
