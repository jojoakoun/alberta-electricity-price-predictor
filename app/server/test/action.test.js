const { getActionKey } = require("../src/utils/action");

describe("Recommendation action keys", () => {
  test.each([
    ["recommended", "run_heavy_appliances"],
    ["acceptable", "use_if_needed"],
    ["avoid", "wait_if_possible"],
  ])("maps %s to %s", (recommendation, expectedAction) => {
    expect(getActionKey(recommendation)).toBe(expectedAction);
  });

  test("rejects an unknown public recommendation", () => {
    expect(() => getActionKey("unknown")).toThrow(
      "Unsupported public recommendation: unknown",
    );
  });
});
