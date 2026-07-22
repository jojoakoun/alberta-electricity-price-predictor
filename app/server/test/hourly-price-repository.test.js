jest.mock("../src/db/pool", () => ({
  pool: {
    query: jest.fn(),
  },
}));

const { pool } = require("../src/db/pool");
const {
  getLatestFinalizedPrice,
  getRecentFinalizedPrices,
} = require("../src/repositories/hourly-price-repository");

describe("Hourly price repository", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns the latest finalized market price", async () => {
    pool.query.mockResolvedValue({
      rows: [
        {
          datetime_utc: "2026-07-18T19:00:00.000Z",
          actual_price: "61.40",
        },
      ],
    });

    await expect(getLatestFinalizedPrice()).resolves.toEqual({
      datetime_utc: "2026-07-18T19:00:00.000Z",
      actual_price: "61.40",
    });
  });

  test("returns null when no finalized market price exists", async () => {
    pool.query.mockResolvedValue({ rows: [] });

    await expect(getLatestFinalizedPrice()).resolves.toBeNull();
  });

  test("loads the default 720-hour market-context window", async () => {
    pool.query.mockResolvedValue({
      rows: [{ actual_price: "20.00" }, { actual_price: "40.00" }],
    });

    const prices = await getRecentFinalizedPrices();

    expect(prices).toEqual([
      { actual_price: "20.00" },
      { actual_price: "40.00" },
    ]);
    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining("LIMIT $1"),
      [720],
    );
  });
});
