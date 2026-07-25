const MINUTE_MS = 60 * 1000;

const PREDICTION_FRESHNESS_POLICY = {
  highConfidenceMaxAgeMs: 75 * MINUTE_MS,
  moderateConfidenceMaxAgeMs: 150 * MINUTE_MS,
};

const OBSERVED_PRICE_FRESHNESS_POLICY = {
  highConfidenceMaxAgeMs: 150 * MINUTE_MS,
  moderateConfidenceMaxAgeMs: 240 * MINUTE_MS,
};

// Forecast source hours and finalized observations have different expected
// publication delays, so their confidence policies must remain separate.

function calculateFreshness(
  timestamp,
  now,
  policy,
  timestampName,
) {
  const timestampDate = new Date(timestamp);
  const currentDate = new Date(now);

  if (
    Number.isNaN(timestampDate.getTime()) ||
    Number.isNaN(currentDate.getTime())
  ) {
    throw new TypeError("Freshness requires valid dates.");
  }

  const ageMs =
    currentDate.getTime() - timestampDate.getTime();

  if (ageMs < 0) {
    throw new RangeError(
      `${timestampName} cannot be in the future.`,
    );
  }

  if (ageMs <= policy.highConfidenceMaxAgeMs) {
    return {
      confidence: "high",
      stale: false,
    };
  }

  if (ageMs <= policy.moderateConfidenceMaxAgeMs) {
    return {
      confidence: "moderate",
      stale: true,
    };
  }

  return {
    confidence: "low",
    stale: true,
  };
}

/** Classify freshness from the forecast's source market-data hour. */
function getPredictionFreshness(
  forecastSourceAt,
  now = new Date(),
) {
  return calculateFreshness(
    forecastSourceAt,
    now,
    PREDICTION_FRESHNESS_POLICY,
    "generatedAt",
  );
}

/** Classify freshness from the latest finalized observed-price hour. */
function getObservedPriceFreshness(
  observedAtUtc,
  now = new Date(),
) {
  return calculateFreshness(
    observedAtUtc,
    now,
    OBSERVED_PRICE_FRESHNESS_POLICY,
    "observedAtUtc",
  );
}

module.exports = {
  getObservedPriceFreshness,
  getPredictionFreshness,
};
