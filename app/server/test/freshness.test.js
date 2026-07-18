const { getFreshness } = require("../src/utils/freshness");

describe("Freshness calculation", () => {
  const now = new Date("2026-07-18T20:00:00.000Z");

  test("returns high confidence through 75 minutes", () => {
    expect(getFreshness("2026-07-18T18:45:00.000Z", now)).toEqual({
      confidence: "high",
      stale: false,
    });
  });

  test("returns moderate confidence through 150 minutes", () => {
    expect(getFreshness("2026-07-18T17:30:00.000Z", now)).toEqual({
      confidence: "moderate",
      stale: true,
    });
  });

  test("returns low confidence after 150 minutes", () => {
    expect(getFreshness("2026-07-18T17:29:59.000Z", now)).toEqual({
      confidence: "low",
      stale: true,
    });
  });

  test("rejects a future generatedAt value", () => {
    expect(() =>
      getFreshness("2026-07-18T20:01:00.000Z", now),
    ).toThrow("generatedAt cannot be in the future.");
  });
});
