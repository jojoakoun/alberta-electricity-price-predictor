const {
  ALBERTA_TIME_ZONE,
  formatAlbertaTime,
} = require("../src/utils/time");

describe("Alberta time formatting", () => {
  test("uses the America/Edmonton timezone", () => {
    expect(ALBERTA_TIME_ZONE).toBe("America/Edmonton");
  });

  test("formats a UTC timestamp in Alberta local time", () => {
    expect(formatAlbertaTime("2026-07-18T21:00:00.000Z")).toBe(
      "3:00 p.m.",
    );
  });

  test("rejects an invalid timestamp", () => {
    expect(() => formatAlbertaTime("invalid")).toThrow(
      "A valid timestamp is required.",
    );
  });
});
