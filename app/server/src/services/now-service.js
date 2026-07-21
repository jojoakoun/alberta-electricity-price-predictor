const {
  getLatestFinalizedPrice,
  getRecentFinalizedPrices,
} = require(
  "../repositories/prediction-repository"
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
 * Build Now from the latest finalized observed price and recent market context.
 *
 * `generatedAt` intentionally equals the observation hour because this
 * recommendation does not depend on a prediction run or worker execution time.
 */
async function getNow() {
  const [
    latestObservedPrice,
    recentPrices,
  ] = await Promise.all([
    getLatestFinalizedPrice(),
    getRecentFinalizedPrices(),
  ]);

  if (!latestObservedPrice) {
    return null;
  }

  const observedDate = new Date(
    latestObservedPrice.datetime_utc,
  );

  if (Number.isNaN(observedDate.getTime())) {
    throw new Error(
      "The latest finalized price has an invalid timestamp.",
    );
  }

  const observedAtUtc = (
    observedDate.toISOString()
  );

  const decision = getCurrentMarketDecision(
    latestObservedPrice.actual_price,
    recentPrices,
  );

  return {
    generatedAt: observedAtUtc,

    ...getObservedPriceFreshness(
      observedAtUtc,
    ),

    price: {
      value: dollarsPerMwhToCentsPerKwh(
        latestObservedPrice.actual_price,
      ),
      unit: "¢/kWh",
      observedAtUtc,
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
