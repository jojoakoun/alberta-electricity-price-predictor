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

module.exports = {
  classifyFutureForecastStatus,
  compareForecastWithObservedPrice,
  getFutureForecasts,
  selectBestTime,
};
