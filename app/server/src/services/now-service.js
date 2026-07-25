const {
  getCurrentMarketPrice,
  getRecentFinalizedPrices,
} = require(
  "../repositories/hourly-price-repository"
);

const {
  dollarsPerMwhToCentsPerKwh,
} = require("../utils/price");

const {
  getObservedPriceFreshness,
} = require("../utils/freshness");

const {
  getCurrentMarketDecision,
} = require("../utils/market-context");

const {
  getActionKey,
} = require("../utils/action");

/**
 * Build Now from the best truthful value available for the current hour.
 *
 * A forecast value remains explicitly labelled as a forecast. The latest
 * finalized observation is used only when the current-hour row is unavailable.
 */
async function getNow(
  viewedAt = new Date(),
) {
  const [
    currentMarketPrice,
    recentPrices,
  ] = await Promise.all([
    getCurrentMarketPrice(viewedAt),
    getRecentFinalizedPrices(),
  ]);

  if (!currentMarketPrice) {
    return null;
  }

  const sourceDate = new Date(
    currentMarketPrice.datetime_utc,
  );

  if (Number.isNaN(sourceDate.getTime())) {
    throw new Error(
      "The current market price has an invalid timestamp.",
    );
  }

  const sourceAtUtc = sourceDate.toISOString();

  const decision = getCurrentMarketDecision(
    currentMarketPrice.price,
    recentPrices,
  );

  return {
    generatedAt: sourceAtUtc,

    ...getObservedPriceFreshness(
      sourceAtUtc,
      viewedAt,
    ),

    price: {
      value: dollarsPerMwhToCentsPerKwh(
        currentMarketPrice.price,
      ),
      unit: "¢/kWh",
      kind: currentMarketPrice.price_kind,
      sourceAtUtc,
    },

    recommendation: {
      level: decision.level,
      explanationKey:
        decision.explanationKey,
      actionKey: getActionKey(
        decision.level,
      ),
    },

    contextKey: decision.contextKey,
  };
}

module.exports = {
  getNow,
};
