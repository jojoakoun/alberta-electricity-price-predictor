jest.mock("../src/db/pool", () => ({
  pool: {
    query: jest.fn(),
  },
}));

const { pool } = require("../src/db/pool");
const {
  getLatestPredictions,
} = require("../src/repositories/prediction-repository");

describe("Prediction repository", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns predictions from the latest successful run", async () => {
    pool.query.mockResolvedValue({
      rows: [
        {
          horizon_hours: 1,
          target_time_utc: "2026-07-18T20:00:00.000Z",
          predicted_price: "84.20",
          recommendation: "Recommended",
          explanation:
            "Predicted price is favorable compared with the recent market.",
          generated_at: "2026-07-18T19:00:00.000Z",
          run_detail: "Application pipeline prediction cycle.",
        },
      ],
    });

    const predictions = await getLatestPredictions();

    expect(predictions).toHaveLength(1);
    expect(predictions[0].horizon_hours).toBe(1);
    expect(pool.query).toHaveBeenCalledTimes(1);
    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining(
        "ORDER BY generated_at DESC, id DESC",
      ),
    );
    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining(
        "lr.detail AS run_detail",
      ),
    );
  });
});
