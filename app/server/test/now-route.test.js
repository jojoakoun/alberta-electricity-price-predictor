jest.mock("../src/services/now-service", () => ({
  getNow: jest.fn(),
}));

const request = require("supertest");

const { getNow } = require("../src/services/now-service");
const { createApp } = require("../src/app");

describe("GET /api/v1/now", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns the current recommendation", async () => {
    getNow.mockResolvedValue({
      recommendation: {
        level: "recommended",
      },
    });

    const response = await request(createApp()).get("/api/v1/now");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      recommendation: {
        level: "recommended",
      },
    });
  });

  test("returns 404 when no prediction exists", async () => {
    getNow.mockResolvedValue(null);

    const response = await request(createApp()).get("/api/v1/now");

    expect(response.status).toBe(404);
  });
});
