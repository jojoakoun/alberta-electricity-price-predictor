const {
  buildForecastTime,
  getTemporalWordingKey,
} = require("../src/utils/forecast-time");

describe("Forecast time presentation", () => {
  test("returns very soon through 90 minutes", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-18T21:30:00.000Z",
        "2026-07-18T20:00:00.000Z",
      ),
    ).toBe("very_soon");
  });

  test("keeps a target visible during the fifteen-minute transition window", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-20T01:00:00.000Z",
        "2026-07-20T01:14:59.000Z",
      ),
    ).toBe("very_soon");
  });

  test("rejects a target outside the transition window", () => {
    expect(() =>
      getTemporalWordingKey(
        "2026-07-20T01:00:00.000Z",
        "2026-07-20T01:15:01.000Z",
      ),
    ).toThrow("Target time is outside the transition window.");
  });

  test("returns in a few hours through four hours", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-18T23:00:00.000Z",
        "2026-07-18T20:00:00.000Z",
      ),
    ).toBe("in_a_few_hours");
  });

  test("returns this afternoon from 12 PM through 5:59 PM Alberta time", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-18T22:00:00.000Z",
        "2026-07-18T16:00:00.000Z",
      ),
    ).toBe("this_afternoon");
  });

  test("returns this evening from 6 PM through 10:59 PM Alberta time", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-19T02:00:00.000Z",
        "2026-07-18T20:00:00.000Z",
      ),
    ).toBe("this_evening");
  });

  test("returns overnight from 11 PM through 5:59 AM Alberta time", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-19T06:00:00.000Z",
        "2026-07-18T20:00:00.000Z",
      ),
    ).toBe("overnight");
  });

  test("returns tomorrow around this time from twenty hours onward", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-19T17:00:00.000Z",
        "2026-07-18T20:00:00.000Z",
      ),
    ).toBe("tomorrow_around_this_time");
  });

  test("uses the morning fallback for an uncovered target", () => {
    expect(
      getTemporalWordingKey(
        "2026-07-18T15:00:00.000Z",
        "2026-07-18T08:00:00.000Z",
      ),
    ).toBe("later_today");
  });

  test("builds UTC, Alberta-local, and wording fields together", () => {
    expect(
      buildForecastTime(
        "2026-07-18T21:00:00.000Z",
        "2026-07-18T20:00:00.000Z",
      ),
    ).toEqual({
      targetTimeUtc: "2026-07-18T21:00:00.000Z",
      targetTimeLocal: "3:00 p.m.",
      temporalWordingKey: "very_soon",
    });
  });
});
