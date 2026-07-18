const { createApp } = require("./app");
const { env } = require("./config/env");

const app = createApp();

const server = app.listen(env.port, env.host, () => {
  console.log(`WattWise API listening on http://${env.host}:${env.port}`);
});

function shutdown(signal) {
  console.log(`${signal} received. Closing HTTP server.`);

  server.close((error) => {
    if (error) {
      console.error("HTTP server shutdown failed.", error);
      process.exitCode = 1;
      return;
    }

    process.exitCode = 0;
  });
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
