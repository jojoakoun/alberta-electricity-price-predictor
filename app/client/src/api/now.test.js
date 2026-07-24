import {
  afterEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { fetchNow } from "./now";


function buildPayload(
  overrides = {},
) {
  const basePayload = {
    generatedAt:
      "2026-07-24T04:00:00.000Z",
    confidence: "high",
    stale: false,

    price: {
      value: 3.87,
      unit: "¢/kWh",
      kind: "forecast",
      sourceAtUtc:
        "2026-07-24T04:00:00.000Z",
    },

    recommendation: {
      level: "acceptable",
      explanationKey:
        "about_average",
      actionKey:
        "use_if_needed",
    },

    contextKey:
      "about_average",
  };

  return {
    ...basePayload,
    ...overrides,

    price: {
      ...basePayload.price,
      ...overrides.price,
    },

    recommendation: {
      ...basePayload.recommendation,
      ...overrides.recommendation,
    },
  };
}


function mockPayload(payload) {
  vi.spyOn(
    globalThis,
    "fetch",
  ).mockResolvedValue(
    new Response(
      JSON.stringify(payload),
      {
        status: 200,

        headers: {
          "Content-Type":
            "application/json",
        },
      },
    ),
  );
}


describe("fetchNow", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test(
    "loads the current-hour public contract",
    async () => {
      const payload = buildPayload();

      mockPayload(payload);

      await expect(
        fetchNow(),
      ).resolves.toEqual(
        payload,
      );

      expect(
        globalThis.fetch,
      ).toHaveBeenCalledWith(
        "/api/v1/now",
        expect.objectContaining({
          headers: {
            Accept:
              "application/json",
          },
        }),
      );
    },
  );

  test(
    "rejects a non-finite current price",
    async () => {
      mockPayload(
        buildPayload({
          price: {
            value: null,
          },
        }),
      );

      await expect(
        fetchNow(),
      ).rejects.toThrow(
        "price.value must be a finite number",
      );
    },
  );

  test(
    "rejects an unsupported current-price kind",
    async () => {
      mockPayload(
        buildPayload({
          price: {
            kind: "live_guess",
          },
        }),
      );

      await expect(
        fetchNow(),
      ).rejects.toThrow(
        "price.kind contains an unsupported value",
      );
    },
  );

  test(
    "rejects an invalid market-hour timestamp",
    async () => {
      mockPayload(
        buildPayload({
          price: {
            sourceAtUtc:
              "not-a-timestamp",
          },
        }),
      );

      await expect(
        fetchNow(),
      ).rejects.toThrow(
        "price.sourceAtUtc must be a valid timestamp",
      );
    },
  );

  test(
    "requires an explicit timezone on generatedAt",
    async () => {
      mockPayload(
        buildPayload({
          generatedAt:
            "2026-07-24T04:00:00",
        }),
      );

      await expect(
        fetchNow(),
      ).rejects.toThrow(
        "generatedAt must be a valid timestamp with an explicit timezone",
      );
    },
  );
});
