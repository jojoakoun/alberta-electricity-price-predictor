const {
  getLatestPredictions,
} = require("../repositories/prediction-repository");

const {
  getLatestFinalizedPrice,
} = require("../repositories/hourly-price-repository");

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

const {
  EXPECTED_HORIZONS,
  parseForecastKinds,
} = require("../domain/forecast-provenance");

const {
  classifyFutureForecastStatus,
  compareForecastWithObservedPrice,
  getFutureForecasts,
  selectBestTime,
} = require("../domain/today-selection");

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
