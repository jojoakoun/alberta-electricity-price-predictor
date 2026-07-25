/** Return a linearly interpolated quantile from sorted finite values. */
function quantile(sortedValues, probability) {
  const position = (
    sortedValues.length - 1
  ) * probability;

  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);

  if (lowerIndex === upperIndex) {
    return sortedValues[lowerIndex];
  }

  const weight = position - lowerIndex;

  return (
    sortedValues[lowerIndex] * (1 - weight)
    + sortedValues[upperIndex] * weight
  );
}

function parseFinitePrice(value, label) {
  const isNumericValue =
    typeof value === "number"
    || (
      typeof value === "string"
      && value.trim() !== ""
    );
  const price = isNumericValue
    ? Number(value)
    : Number.NaN;

  if (!Number.isFinite(price)) {
    throw new TypeError(
      `${label} must be a finite number.`,
    );
  }

  return price;
}

function normalizeMarketPrices(
  currentPrice,
  recentPriceRows,
) {
  if (!Array.isArray(recentPriceRows)) {
    throw new TypeError(
      "Recent finalized prices must be an array.",
    );
  }

  if (recentPriceRows.length === 0) {
    throw new Error(
      "Recent finalized prices are required.",
    );
  }

  const price = parseFinitePrice(
    currentPrice,
    "Current price",
  );

  // A malformed persisted value must fail visibly; dropping it would silently
  // change the market distribution and potentially the recommendation.
  const recentPrices = recentPriceRows
    .map((row, index) =>
      parseFinitePrice(
        row && row.actual_price,
        `Recent finalized price at index ${index}`,
      ),
    )
    .sort((left, right) => left - right);

  return {
    price,
    recentPrices,
  };
}

function classifyMarketContext(
  price,
  firstQuartile,
  thirdQuartile,
) {
  if (price <= firstQuartile) {
    return "lower_than_usual";
  }

  if (price >= thirdQuartile) {
    return "higher_than_usual";
  }

  return "about_average";
}

function buildMarketThresholds(
  currentPrice,
  recentPriceRows,
) {
  const {
    price,
    recentPrices,
  } = normalizeMarketPrices(
    currentPrice,
    recentPriceRows,
  );

  const firstQuartile = quantile(
    recentPrices,
    0.25,
  );

  const thirdQuartile = quantile(
    recentPrices,
    0.75,
  );

  const interquartileRange = (
    thirdQuartile - firstQuartile
  );

  return {
    price,
    firstQuartile,
    thirdQuartile,
    avoidThreshold: (
      thirdQuartile
      + 1.5 * interquartileRange
    ),
  };
}

function getMarketContext(
  currentPrice,
  recentPriceRows,
) {
  const {
    price,
    firstQuartile,
    thirdQuartile,
  } = buildMarketThresholds(
    currentPrice,
    recentPriceRows,
  );

  return classifyMarketContext(
    price,
    firstQuartile,
    thirdQuartile,
  );
}

/**
 * Classify the latest observed price against recent finalized market prices.
 *
 * The Tukey upper fence reserves "avoid" for an unusually extreme price,
 * while the quartiles provide the ordinary consumer market context.
 */
function getCurrentMarketDecision(
  currentPrice,
  recentPriceRows,
) {
  const {
    price,
    firstQuartile,
    thirdQuartile,
    avoidThreshold,
  } = buildMarketThresholds(
    currentPrice,
    recentPriceRows,
  );

  const contextKey = classifyMarketContext(
    price,
    firstQuartile,
    thirdQuartile,
  );

  if (price >= avoidThreshold) {
    return {
      contextKey,
      level: "avoid",
      explanationKey: "higher_than_usual",
    };
  }

  if (price <= firstQuartile) {
    return {
      contextKey,
      level: "recommended",
      explanationKey: "lower_than_usual",
    };
  }

  return {
    contextKey,
    level: "acceptable",
    explanationKey: "about_average",
  };
}

module.exports = {
  getCurrentMarketDecision,
  getMarketContext,
};
