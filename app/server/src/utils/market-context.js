function quantile(sortedValues, probability) {
  const position = (sortedValues.length - 1) * probability;
  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);

  if (lowerIndex === upperIndex) {
    return sortedValues[lowerIndex];
  }

  const weight = position - lowerIndex;

  return (
    sortedValues[lowerIndex] * (1 - weight) +
    sortedValues[upperIndex] * weight
  );
}

function getMarketContext(currentPrice, recentPriceRows) {
  const price = Number(currentPrice);
  const recentPrices = recentPriceRows
    .map((row) => Number(row.actual_price))
    .filter(Number.isFinite)
    .sort((left, right) => left - right);

  if (!Number.isFinite(price)) {
    throw new TypeError("Current price must be a finite number.");
  }

  if (recentPrices.length === 0) {
    throw new Error("Recent finalized prices are required.");
  }

  // Quartiles compare the current price with the observed 720-hour market.
  const firstQuartile = quantile(recentPrices, 0.25);
  const thirdQuartile = quantile(recentPrices, 0.75);

  if (price <= firstQuartile) {
    return "lower_than_usual";
  }

  if (price >= thirdQuartile) {
    return "higher_than_usual";
  }

  return "about_average";
}

module.exports = {
  getMarketContext,
};
