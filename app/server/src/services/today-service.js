const {
  getLatestPredictions,
} = require("../repositories/prediction-repository");

const {
  getExplanationKey,
} = require("../utils/explanation");

const {
  buildForecastTime,
} = require("../utils/forecast-time");

const {
  getFreshness,
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

function buildPublicForecast(
  prediction,
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
  };
}

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

function selectBestTime(
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

  return forecasts
    .filter(
      (forecast) =>
        new Date(
          forecast.targetTimeUtc,
        ).getTime()
        > viewedDate.getTime(),
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

async function getToday(
  viewedAt = new Date(),
) {
  const predictions =
    await getLatestPredictions();

  if (predictions.length === 0) {
    return null;
  }

  validateForecastSet(predictions);

  const forecasts = predictions.map(
    (prediction) =>
      buildPublicForecast(
        prediction,
        viewedAt,
      ),
  );

  const generatedAt = new Date(
    predictions[0].generated_at,
  ).toISOString();

  const freshness = getFreshness(
    predictions[0].generated_at,
    viewedAt,
  );

  const bestForecast =
    selectBestTime(
      forecasts,
      viewedAt,
    );

  return {
    generatedAt,
    ...(
      bestForecast
        ? freshness
        : {
            confidence: "low",
            stale: true,
          }
    ),
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
