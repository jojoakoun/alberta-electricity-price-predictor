const {
  EXPECTED_HORIZONS,
  parseForecastKinds,
} = require("../src/domain/forecast-provenance");

const VERSIONED_FORECAST_KINDS = {
  1: "model_forecast",
  3: "model_forecast",
  6: "model_forecast",
  12: "model_forecast",
  24: "persistence_reference",
};

function buildPredictions(runDetail) {
  return EXPECTED_HORIZONS.map(
    (horizon) => ({
      horizon_hours: horizon,
      run_detail: runDetail,
    }),
  );
}

describe("Forecast provenance", () => {
  test("parses the complete versioned forecast-kind contract", () => {
    const runDetail = JSON.stringify({
      schemaVersion: 1,
      forecastKinds: VERSIONED_FORECAST_KINDS,
    });

    expect(
      Array.from(
        parseForecastKinds(
          buildPredictions(runDetail),
        ).entries(),
      ),
    ).toEqual([
      [1, "model_forecast"],
      [3, "model_forecast"],
      [6, "model_forecast"],
      [12, "model_forecast"],
      [24, "persistence_reference"],
    ]);
  });

  test("preserves the verified pre-metadata persistence lineage", () => {
    const forecastKinds = parseForecastKinds(
      buildPredictions(
        "Application pipeline prediction cycle.",
      ),
    );

    expect(forecastKinds.get(1)).toBe("model_forecast");
    expect(forecastKinds.get(24)).toBe(
      "persistence_reference",
    );
  });

  test("fails closed for unverified legacy summaries", () => {
    const forecastKinds = parseForecastKinds(
      buildPredictions("Unrecognized legacy run."),
    );

    expect(
      Array.from(forecastKinds.values()),
    ).toEqual([
      "unknown",
      "unknown",
      "unknown",
      "unknown",
      "unknown",
    ]);
  });

  test("rejects inconsistent metadata within one run", () => {
    const predictions = buildPredictions(
      "Application pipeline prediction cycle.",
    );
    predictions[4].run_detail = "Different detail.";

    expect(
      () => parseForecastKinds(predictions),
    ).toThrow(
      "The latest prediction run contains inconsistent forecast metadata.",
    );
  });

  test("preserves the invalid-JSON error and its cause", () => {
    let receivedError;

    try {
      parseForecastKinds(
        buildPredictions("{not-json"),
      );
    } catch (error) {
      receivedError = error;
    }

    expect(receivedError).toBeInstanceOf(Error);
    expect(receivedError.message).toBe(
      "The latest prediction run has invalid forecast metadata.",
    );
    expect(receivedError.cause).toBeInstanceOf(SyntaxError);
  });

  test("rejects unsupported metadata schemas", () => {
    const runDetail = JSON.stringify({
      schemaVersion: 2,
      forecastKinds: VERSIONED_FORECAST_KINDS,
    });

    expect(
      () => parseForecastKinds(
        buildPredictions(runDetail),
      ),
    ).toThrow(
      "The latest prediction run has unsupported forecast metadata.",
    );
  });

  test("rejects incomplete horizon metadata", () => {
    const runDetail = JSON.stringify({
      schemaVersion: 1,
      forecastKinds: {
        1: "model_forecast",
        3: "model_forecast",
        6: "model_forecast",
        12: "model_forecast",
      },
    });

    expect(
      () => parseForecastKinds(
        buildPredictions(runDetail),
      ),
    ).toThrow(
      "The latest prediction run has incomplete forecast metadata.",
    );
  });

  test("rejects unsupported forecast kinds by horizon", () => {
    const runDetail = JSON.stringify({
      schemaVersion: 1,
      forecastKinds: {
        ...VERSIONED_FORECAST_KINDS,
        24: "unverified_baseline",
      },
    });

    expect(
      () => parseForecastKinds(
        buildPredictions(runDetail),
      ),
    ).toThrow(
      "The latest prediction run has an unsupported forecast kind for 24h.",
    );
  });
});
