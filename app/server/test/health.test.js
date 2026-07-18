const request = require("supertest");

const { createApp } = require("../src/app");

describe("Health endpoint", () => {
  test("GET /api/v1/health returns HTTP 200", async () => {
    const response = await request(createApp()).get("/api/v1/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: "ok",
    });
  });
});
