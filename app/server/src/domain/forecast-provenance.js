const EXPECTED_HORIZONS = Object.freeze([
  1,
  3,
  6,
  12,
  24,
]);

const SUPPORTED_VERSIONED_FORECAST_KINDS = new Set([
  "model_forecast",
  "persistence_reference",
]);

const LEGACY_PERSISTENCE_RUN_DETAIL =
  "Application pipeline prediction cycle.";

function getVerifiedLegacyForecastKinds() {
  return new Map(
    EXPECTED_HORIZONS.map(
      (horizon) => [
        horizon,
        horizon === 24
          ? "persistence_reference"
          : "model_forecast",
      ],
    ),
  );
}

function getUnknownForecastKinds() {
  return new Map(
    EXPECTED_HORIZONS.map(
      (horizon) => [horizon, "unknown"],
    ),
  );
}

/**
 * Resolve each horizon's provenance from one run's persisted metadata.
 *
 * The one verified pre-metadata lineage is mapped explicitly. Other legacy
 * summaries remain visible as unknown and therefore cannot produce savings.
 */
function parseForecastKinds(predictions) {
  const runDetails = new Set(
    predictions.map(
      (prediction) =>
        prediction.run_detail ?? null,
    ),
  );

  if (runDetails.size !== 1) {
    throw new Error(
      "The latest prediction run contains inconsistent forecast metadata.",
    );
  }

  const [runDetail] = runDetails;

  // Runs created before semantic metadata was added used this exact summary.
  // Both the pre-metadata and current active 24-hour lineages are verified
  // as the same persistence rule.
  if (
    runDetail
    === LEGACY_PERSISTENCE_RUN_DETAIL
  ) {
    return getVerifiedLegacyForecastKinds();
  }

  if (
    typeof runDetail !== "string"
    || !runDetail.trim().startsWith("{")
  ) {
    return getUnknownForecastKinds();
  }

  let metadata;

  try {
    metadata = JSON.parse(runDetail);
  } catch (error) {
    throw new Error(
      "The latest prediction run has invalid forecast metadata.",
      { cause: error },
    );
  }

  if (
    metadata === null
    || metadata.schemaVersion !== 1
    || typeof metadata.forecastKinds !== "object"
    || metadata.forecastKinds === null
  ) {
    throw new Error(
      "The latest prediction run has unsupported forecast metadata.",
    );
  }

  const metadataHorizons = Object.keys(
    metadata.forecastKinds,
  ).map(Number);

  const hasExpectedHorizons =
    metadataHorizons.length
      === EXPECTED_HORIZONS.length
    && EXPECTED_HORIZONS.every(
      (horizon) =>
        metadataHorizons.includes(horizon),
    );

  if (!hasExpectedHorizons) {
    throw new Error(
      "The latest prediction run has incomplete forecast metadata.",
    );
  }

  return new Map(
    EXPECTED_HORIZONS.map((horizon) => {
      const forecastKind =
        metadata.forecastKinds[horizon];

      if (
        !SUPPORTED_VERSIONED_FORECAST_KINDS
          .has(forecastKind)
      ) {
        throw new Error(
          `The latest prediction run has an unsupported forecast kind for ${horizon}h.`,
        );
      }

      return [horizon, forecastKind];
    }),
  );
}

module.exports = {
  EXPECTED_HORIZONS,
  parseForecastKinds,
};
