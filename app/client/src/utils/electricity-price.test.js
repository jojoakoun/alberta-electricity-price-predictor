import {
  describe,
  expect,
  test,
} from "vitest";

import {
  formatElectricityPrice,
} from "./electricity-price";

describe("electricity price formatting", () => {
  test("keeps an exact zero explicit", () => {
    expect(
      formatElectricityPrice(0),
    ).toBe("≤0.01");
  });

  test("marks a small positive price as below one hundredth", () => {
    expect(
      formatElectricityPrice(0.002),
    ).toBe("≤0.01");
  });

  test("formats ordinary prices to two decimal places", () => {
    expect(
      formatElectricityPrice(1.417),
    ).toBe("1.42");
  });

  test("rejects invalid values", () => {
    expect(
      () => formatElectricityPrice("invalid"),
    ).toThrow(
      "Electricity price must be a finite number.",
    );
  });
});
