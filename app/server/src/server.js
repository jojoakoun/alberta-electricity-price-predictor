const { createApp } = require("./app");
const { env } = require("./config/env");
const { pool } = require("./db/pool");

const app = createApp();

const server = app.listen(env.port, env.host, () => {
  console.log(`WattWise API listening on http://${env.host}:${env.port}`);
});

let isShuttingDown = false;

async function shutdown(signal) {
  if (isShuttingDown) {
    return;
  }

  isShuttingDown = true;

  console.log(`${signal} received. Closing WattWise API.`);

  server.close(async (serverError) => {
    try {
      // Release database connections so local reloads and production shutdowns
      // both leave the process cleanly after the listener stops accepting work.
      await pool.end();
    } catch (poolError) {
      console.error("PostgreSQL pool shutdown failed.", poolError);
      process.exitCode = 1;
      return;
    }

    if (serverError) {
      console.error("HTTP server shutdown failed.", serverError);
      process.exitCode = 1;
      return;
    }

    process.exitCode = 0;
  });
}

process.on("SIGINT", () => {
  void shutdown("SIGINT");
});

process.on("SIGTERM", () => {
  void shutdown("SIGTERM");
});
