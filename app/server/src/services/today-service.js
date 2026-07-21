const {
  getLatestFinalizedPrice,
  getLatestPredictions,
} = require("../repositories/prediction-repository");

const {
  getExplanationKey,
} = require("../utils/explanation");

const {
  buildForecastTime,
} = require("../utils/forecast-time");

const {
  getPredictionFreshness,
} = require("../utils/freshness");

const {
  dollarsPerMwhToCentsPerKwh,
} = require("../utils/price");

const {
  normalizeRecommendation,
} = require("../utils/recommendation");

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

function validateForecastSet(predictions) {
  const horizons = predictions.map(
    (prediction) =>
      prediction.horizon_hours,
  );

  const isComplete =
    horizons.length
      === EXPECTED_HORIZONS.length
    && EXPECTED_HORIZONS.every(
      (horizon, index) =>
        horizons[index] === horizon,
    );

  if (!isComplete) {
    throw new Error(
      "The latest prediction run does not contain the five expected horizons.",
    );
  }
}

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

function buildPublicForecast(
  prediction,
  forecastKind,
  viewedAt,
) {
  return {
    horizonHours: prediction.horizon_hours,
    ...buildForecastTime(
      prediction.target_time_utc,
      viewedAt,
    ),
    priceCents:
      dollarsPerMwhToCentsPerKwh(
        prediction.predicted_price,
      ),
    recommendation:
      normalizeRecommendation(
        prediction.recommendation,
      ),
    explanationKey:
      getExplanationKey(
        prediction.explanation,
      ),
    forecastKind,
  };
}

/** Exclude passed targets before selecting a future planning opportunity. */
function getFutureForecasts(
  forecasts,
  viewedAt,
) {
  const viewedDate = new Date(
    viewedAt,
  );

  if (
    Number.isNaN(
      viewedDate.getTime(),
    )
  ) {
    throw new TypeError(
      "Best-time selection requires a valid viewedAt timestamp.",
    );
  }

  return forecasts.filter(
    (forecast) =>
      new Date(
        forecast.targetTimeUtc,
      ).getTime()
      > viewedDate.getTime(),
  );
}

/**
 * Select the lowest eligible model forecast.
 *
 * Persistence references stay in the timeline for context but cannot become a
 * best-time or savings claim because they repeat an observed price by design.
 */
function selectBestTime(forecasts) {
  return forecasts
    .filter(
      (forecast) =>
        forecast.forecastKind
        === "model_forecast",
    )
    .reduce(
      (best, forecast) => {
        if (
          !best
          || forecast.priceCents
            < best.priceCents
        ) {
          return forecast;
        }

        return best;
      },
      null,
    );
}

function classifyFutureForecastStatus(
  futureForecasts,
  bestForecast,
) {
  if (futureForecasts.length === 0) {
    return "none_remaining";
  }

  if (bestForecast) {
    return "available";
  }

  if (
    futureForecasts.every(
      (forecast) =>
        forecast.forecastKind
        === "persistence_reference",
    )
  ) {
    return "reference_only";
  }

  return "provenance_unavailable";
}

function buildObservedPrice(latestPrice) {
  if (!latestPrice) {
    return {
      currentPriceCents: null,
      currentObservedAtUtc: null,
    };
  }

  const observedDate = new Date(
    latestPrice.datetime_utc,
  );

  if (Number.isNaN(observedDate.getTime())) {
    throw new Error(
      "The latest finalized price has an invalid timestamp.",
    );
  }

  return {
    currentPriceCents:
      dollarsPerMwhToCentsPerKwh(
        latestPrice.actual_price,
      ),
    currentObservedAtUtc:
      observedDate.toISOString(),
  };
}

/**
 * Compare the best eligible forecast with the current observed public price.
 * Both values are already rounded to cents per kWh, so equality matches what
 * the consumer sees instead of creating sub-display precision savings.
 */
function compareForecastWithObservedPrice(
  bestForecast,
  currentPriceCents,
) {
  if (
    !bestForecast
    || currentPriceCents === null
  ) {
    return {
      comparison: "unavailable",
      priceDifferenceCents: null,
    };
  }

  const priceDifferenceCents = Number(
    Math.abs(
      bestForecast.priceCents
      - currentPriceCents,
    ).toFixed(2),
  );

  if (
    bestForecast.priceCents
    < currentPriceCents
  ) {
    return {
      comparison: "forecast_lower",
      priceDifferenceCents,
    };
  }

  if (
    bestForecast.priceCents
    > currentPriceCents
  ) {
    return {
      comparison: "current_lower",
      priceDifferenceCents,
    };
  }

  return {
    comparison: "forecast_equal",
    priceDifferenceCents: 0,
  };
}

/**
 * Build the Today response from one complete successful prediction run.
 *
 * The server owns target eligibility, provenance, best-time selection, and the
 * observed-price comparison so the browser never reconstructs these rules.
 */
async function getToday(
  viewedAt = new Date(),
) {
  const [predictions, latestPrice] =
    await Promise.all([
      getLatestPredictions(),
      getLatestFinalizedPrice(),
    ]);

  if (predictions.length === 0) {
    return null;
  }

  validateForecastSet(predictions);

  const forecastKinds =
    parseForecastKinds(predictions);

  const forecasts = predictions.map(
    (prediction) =>
      buildPublicForecast(
        prediction,
        forecastKinds.get(
          prediction.horizon_hours,
        ),
        viewedAt,
      ),
  );

  const forecastSourceAt = new Date(
    predictions[0].generated_at,
  ).toISOString();

  const freshness = getPredictionFreshness(
    predictions[0].generated_at,
    viewedAt,
  );

  const futureForecasts =
    getFutureForecasts(
      forecasts,
      viewedAt,
    );

  const bestForecast =
    selectBestTime(
      futureForecasts,
    );

  const futureForecastStatus =
    classifyFutureForecastStatus(
      futureForecasts,
      bestForecast,
    );

  const observedPrice =
    buildObservedPrice(latestPrice);

  const comparison = compareForecastWithObservedPrice(
    bestForecast,
    observedPrice.currentPriceCents,
  );

  return {
    generatedAt: forecastSourceAt,
    ...freshness,
    futureForecastStatus,
    ...comparison,
    ...observedPrice,
    forecasts,
    bestTime: bestForecast
      ? {
          horizonHours:
            bestForecast.horizonHours,
          targetTimeUtc:
            bestForecast.targetTimeUtc,
          targetTimeLocal:
            bestForecast.targetTimeLocal,
          priceCents:
            bestForecast.priceCents,
          recommendation:
            bestForecast.recommendation,
        }
      : null,
  };
}

module.exports = {
  getToday,
};
