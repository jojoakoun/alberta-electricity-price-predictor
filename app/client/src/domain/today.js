/**
 * Return whether the API proved a lower-price planning opportunity.
 *
 * The server owns the comparison. The browser only renders its result and
 * must not independently select a forecast or infer savings.
 */
export function isLowerPriceOpportunity(comparison) {
  return comparison === "forecast_lower";
}


/**
 * Keep only forecast targets that remain actionable after the current
 * market-price reference hour.
 */
export function getActionableForecasts(
  forecasts,
  currentPriceSourceAtUtc,
) {
  if (!Array.isArray(forecasts)) {
    throw new TypeError(
      "Today forecasts must be an array.",
    );
  }

  if (!currentPriceSourceAtUtc) {
    return forecasts;
  }

  const referenceTime = new Date(
    currentPriceSourceAtUtc,
  ).getTime();

  if (!Number.isFinite(referenceTime)) {
    throw new TypeError(
      "Current price source time must be valid.",
    );
  }

  return forecasts.filter(
    (forecast) => {
      const targetTime = new Date(
        forecast.targetTimeUtc,
      ).getTime();

      return (
        Number.isFinite(targetTime)
        && targetTime > referenceTime
      );
    },
  );
}
