const request = require("supertest");

const { createApp } = require("../src/app");

describe("Express application foundation", () => {
  let app;

  beforeAll(() => {
    app = createApp();
  });

  test("returns the public error contract for an unknown route", async () => {
    const response = await request(app).get("/unknown-route");

    expect(response.status).toBe(404);
    expect(response.body).toEqual({
      error: {
        code: "NOT_FOUND",
        message: "The requested resource was not found.",
      },
    });
  });

  test("adds security headers and hides the Express signature", async () => {
    const response = await request(app).get("/unknown-route");

    expect(response.headers["x-content-type-options"]).toBe("nosniff");
    expect(response.headers["x-powered-by"]).toBeUndefined();
  });

  test("allows GET requests from the configured frontend origin", async () => {
    const response = await request(app)
      .get("/unknown-route")
      .set("Origin", "http://localhost:5173");

    expect(response.headers["access-control-allow-origin"]).toBe(
      "http://localhost:5173",
    );
  });
});
