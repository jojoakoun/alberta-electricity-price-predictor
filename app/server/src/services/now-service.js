const {
  getLatestPredictions,
  getLatestFinalizedPrice,
  getRecentFinalizedPrices,
} = require("../repositories/prediction-repository");

const {
  dollarsPerMwhToCentsPerKwh,
} = require("../utils/price");

const {
  normalizeRecommendation,
} = require("../utils/recommendation");

const {
  getExplanationKey,
} = require("../utils/explanation");

const {
  getFreshness,
} = require("../utils/freshness");

const {
  getMarketContext,
} = require("../utils/market-context");

const {
  getActionKey,
} = require("../utils/action");

async function getNow() {
  const predictions = await getLatestPredictions();

  if (predictions.length === 0) {
    return null;
  }

  const prediction = predictions.find(
    (row) => row.horizon_hours === 1,
  );

  if (!prediction) {
    throw new Error("The latest prediction run is missing the 1-hour forecast.");
  }

  const latestPrice = await getLatestFinalizedPrice();

  if (!latestPrice) {
    throw new Error("No finalized market price is available.");
  }

  const recentPrices = await getRecentFinalizedPrices();

  const observedAtUtc = latestPrice.datetime_utc
    ? new Date(latestPrice.datetime_utc).toISOString()
    : undefined;

  const recommendation = normalizeRecommendation(
    prediction.recommendation,
  );

  return {
    generatedAt: prediction.generated_at,
    ...getFreshness(prediction.generated_at),

    price: {
      value: dollarsPerMwhToCentsPerKwh(
        latestPrice.actual_price,
      ),
      unit: "¢/kWh",
      ...(observedAtUtc
        ? { observedAtUtc }
        : {}),
    },

    recommendation: {
      level: recommendation,
      explanationKey: getExplanationKey(
        prediction.explanation,
      ),
      actionKey: getActionKey(recommendation),
    },

    contextKey: getMarketContext(
      latestPrice.actual_price,
      recentPrices,
    ),
  };
}

module.exports = {
  getNow,
};
