const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const request = require("supertest");

const {
  createApp,
} = require("../src/app");

describe("production web application", () => {
  let clientDistPath;

  beforeEach(() => {
    clientDistPath = fs.mkdtempSync(
      path.join(
        os.tmpdir(),
        "wattwise-client-",
      ),
    );

    fs.writeFileSync(
      path.join(
        clientDistPath,
        "index.html",
      ),
      [
        "<!doctype html>",
        "<html>",
        "<body>",
        '<div id="root">WattWise</div>',
        "</body>",
        "</html>",
      ].join(""),
    );

    fs.mkdirSync(
      path.join(
        clientDistPath,
        "assets",
      ),
    );

    fs.writeFileSync(
      path.join(
        clientDistPath,
        "assets",
        "application.js",
      ),
      "console.log('WattWise');",
    );
  });

  afterEach(() => {
    fs.rmSync(
      clientDistPath,
      {
        recursive: true,
        force: true,
      },
    );
  });

  test("serves the React entry page", async () => {
    const response = await request(
      createApp({
        nodeEnv: "production",
        clientDistPath,
        enableRequestLogging: false,
      }),
    ).get("/");

    expect(response.status).toBe(200);
    expect(response.type).toMatch(/html/);
    expect(response.text).toContain("WattWise");
  });

  test("uses the React entry page for SPA routes", async () => {
    const app = createApp({
      nodeEnv: "production",
      clientDistPath,
      enableRequestLogging: false,
    });

    for (const route of [
      "/today",
      "/learn",
      "/project",
    ]) {
      const response = await request(app).get(route);

      expect(response.status).toBe(200);
      expect(response.type).toMatch(/html/);
      expect(response.text).toContain("WattWise");
    }
  });

  test("serves built frontend assets", async () => {
    const response = await request(
      createApp({
        nodeEnv: "production",
        clientDistPath,
        enableRequestLogging: false,
      }),
    ).get("/assets/application.js");

    expect(response.status).toBe(200);
    expect(response.type).toMatch(
      /javascript/,
    );
  });

  test("does not redirect unknown API routes to React", async () => {
    const response = await request(
      createApp({
        nodeEnv: "production",
        clientDistPath,
        enableRequestLogging: false,
      }),
    ).get("/api/v1/unknown");

    expect(response.status).toBe(404);
    expect(response.type).toMatch(/json/);
  });
});
