import {
  describe,
  expect,
  test,
} from "vitest";

import {
  getActionableForecasts,
} from "./today";


describe("getActionableForecasts", () => {
  test(
    "removes targets at or before the current market-price hour",
    () => {
      const forecasts = [
        {
          horizonHours: 1,
          targetTimeUtc:
            "2026-07-24T04:00:00.000Z",
        },
        {
          horizonHours: 3,
          targetTimeUtc:
            "2026-07-24T06:00:00.000Z",
        },
        {
          horizonHours: 6,
          targetTimeUtc:
            "2026-07-24T09:00:00.000Z",
        },
      ];

      expect(
        getActionableForecasts(
          forecasts,
          "2026-07-24T05:00:00.000Z",
        ),
      ).toEqual([
        forecasts[1],
        forecasts[2],
      ]);
    },
  );

  test(
    "does not mutate the complete API forecast set",
    () => {
      const forecasts = [
        {
          horizonHours: 1,
          targetTimeUtc:
            "2026-07-24T04:00:00.000Z",
        },
        {
          horizonHours: 3,
          targetTimeUtc:
            "2026-07-24T06:00:00.000Z",
        },
      ];

      getActionableForecasts(
        forecasts,
        "2026-07-24T05:00:00.000Z",
      );

      expect(
        forecasts,
      ).toHaveLength(2);
    },
  );
});
