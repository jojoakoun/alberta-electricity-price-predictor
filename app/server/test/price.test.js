const {
  dollarsPerMwhToCentsPerKwh,
} = require("../src/utils/price");

describe("Price conversion", () => {
  test("converts dollars per MWh to cents per kWh", () => {
    expect(dollarsPerMwhToCentsPerKwh("84.20")).toBe(8.42);
    expect(dollarsPerMwhToCentsPerKwh(61.4)).toBe(6.14);
  });

  test("preserves enough precision for small public prices", () => {
    expect(dollarsPerMwhToCentsPerKwh(33.333)).toBe(3.3333);
    expect(dollarsPerMwhToCentsPerKwh(0.02)).toBe(0.002);
    expect(dollarsPerMwhToCentsPerKwh(0)).toBe(0);
  });

  test("rejects an invalid price", () => {
    expect(() => dollarsPerMwhToCentsPerKwh("invalid")).toThrow(
      "Price must be a finite number.",
    );
  });
});
