export const SUPPORTED_FORECAST_HORIZONS_HOURS = Object.freeze([
  1,
  3,
  6,
  12,
  24,
]);

const TIMESTAMP_WITH_TIMEZONE_PATTERN = (
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$/
);

const CONFIDENCE_LEVELS = new Set([
  "high",
  "moderate",
  "low",
]);

const RECOMMENDATION_LEVELS = new Set([
  "recommended",
  "acceptable",
  "avoid",
]);

const EXPLANATION_KEYS = new Set([
  "lower_than_usual",
  "about_average",
  "acceptable_market_risk",
  "higher_than_usual",
]);

const TEMPORAL_WORDING_KEYS = new Set([
  "recently_passed",
  "very_soon",
  "in_a_few_hours",
  "this_afternoon",
  "this_evening",
  "overnight",
  "later_today",
  "tomorrow_around_this_time",
]);

const FORECAST_KINDS = new Set([
  "model_forecast",
  "persistence_reference",
  "unknown",
]);

const TODAY_COMPARISON_STATES = new Set([
  "forecast_lower",
  "forecast_equal",
  "current_lower",
  "unavailable",
]);

const FUTURE_FORECAST_STATES = new Set([
  "available",
  "none_remaining",
  "reference_only",
  "provenance_unavailable",
]);

const ACTION_KEYS = new Set([
  "run_heavy_appliances",
  "use_if_needed",
  "wait_if_possible",
]);

const MARKET_CONTEXT_KEYS = new Set([
  "lower_than_usual",
  "about_average",
  "higher_than_usual",
]);

function failContract(contractName, fieldPath, expectation) {
  throw new TypeError(
    `Invalid ${contractName} API response: ${fieldPath} ${expectation}.`,
  );
}

function requireObject(value, contractName, fieldPath) {
  if (
    value === null
    || typeof value !== "object"
    || Array.isArray(value)
  ) {
    failContract(contractName, fieldPath, "must be an object");
  }

  return value;
}

function requireBoolean(value, contractName, fieldPath) {
  if (typeof value !== "boolean") {
    failContract(contractName, fieldPath, "must be a boolean");
  }
}

function requireFiniteNumber(value, contractName, fieldPath) {
  if (!Number.isFinite(value)) {
    failContract(contractName, fieldPath, "must be a finite number");
  }
}

function requireNonEmptyString(value, contractName, fieldPath) {
  if (typeof value !== "string" || value.trim() === "") {
    failContract(contractName, fieldPath, "must be a non-empty string");
  }
}

function requireTimestamp(value, contractName, fieldPath) {
  requireNonEmptyString(value, contractName, fieldPath);

  const hasExplicitTimezone = (
    TIMESTAMP_WITH_TIMEZONE_PATTERN.test(value)
  );

  if (!hasExplicitTimezone || Number.isNaN(Date.parse(value))) {
    failContract(
      contractName,
      fieldPath,
      "must be a valid timestamp with an explicit timezone",
    );
  }
}

function requireKnownValue(
  value,
  allowedValues,
  contractName,
  fieldPath,
) {
  if (!allowedValues.has(value)) {
    failContract(contractName, fieldPath, "contains an unsupported value");
  }
}

function requireNullableFiniteNumber(value, contractName, fieldPath) {
  if (value !== null) {
    requireFiniteNumber(value, contractName, fieldPath);
  }
}

function requireNullableTimestamp(value, contractName, fieldPath) {
  if (value !== null) {
    requireTimestamp(value, contractName, fieldPath);
  }
}

function validatePublicRecommendation(value, contractName, fieldPath) {
  requireKnownValue(
    value,
    RECOMMENDATION_LEVELS,
    contractName,
    fieldPath,
  );
}

function validateTodayForecast(forecast, index) {
  const fieldPath = `forecasts[${index}]`;
  const forecastPoint = requireObject(
    forecast,
    "Today",
    fieldPath,
  );

  requireFiniteNumber(
    forecastPoint.horizonHours,
    "Today",
    `${fieldPath}.horizonHours`,
  );
  requireTimestamp(
    forecastPoint.targetTimeUtc,
    "Today",
    `${fieldPath}.targetTimeUtc`,
  );
  requireNonEmptyString(
    forecastPoint.targetTimeLocal,
    "Today",
    `${fieldPath}.targetTimeLocal`,
  );
  requireKnownValue(
    forecastPoint.temporalWordingKey,
    TEMPORAL_WORDING_KEYS,
    "Today",
    `${fieldPath}.temporalWordingKey`,
  );
  requireFiniteNumber(
    forecastPoint.priceCents,
    "Today",
    `${fieldPath}.priceCents`,
  );
  validatePublicRecommendation(
    forecastPoint.recommendation,
    "Today",
    `${fieldPath}.recommendation`,
  );
  requireKnownValue(
    forecastPoint.explanationKey,
    EXPLANATION_KEYS,
    "Today",
    `${fieldPath}.explanationKey`,
  );
  requireKnownValue(
    forecastPoint.forecastKind,
    FORECAST_KINDS,
    "Today",
    `${fieldPath}.forecastKind`,
  );

  return forecastPoint;
}

function validateBestTime(bestTime, forecasts) {
  if (bestTime === null) {
    return;
  }

  const selectedForecast = requireObject(
    bestTime,
    "Today",
    "bestTime",
  );

  requireFiniteNumber(
    selectedForecast.horizonHours,
    "Today",
    "bestTime.horizonHours",
  );
  requireTimestamp(
    selectedForecast.targetTimeUtc,
    "Today",
    "bestTime.targetTimeUtc",
  );
  requireNonEmptyString(
    selectedForecast.targetTimeLocal,
    "Today",
    "bestTime.targetTimeLocal",
  );
  requireFiniteNumber(
    selectedForecast.priceCents,
    "Today",
    "bestTime.priceCents",
  );
  validatePublicRecommendation(
    selectedForecast.recommendation,
    "Today",
    "bestTime.recommendation",
  );

  const matchingForecast = forecasts.find(
    (forecast) => (
      forecast.horizonHours === selectedForecast.horizonHours
      && forecast.targetTimeUtc === selectedForecast.targetTimeUtc
      && forecast.targetTimeLocal === selectedForecast.targetTimeLocal
      && forecast.priceCents === selectedForecast.priceCents
      && forecast.recommendation === selectedForecast.recommendation
    ),
  );

  if (!matchingForecast) {
    failContract(
      "Today",
      "bestTime",
      "must match one forecast point",
    );
  }

  // Provenance is server-owned. The browser may display a persistence point,
  // but it must reject a payload that promotes one as a savings opportunity.
  if (matchingForecast.forecastKind !== "model_forecast") {
    failContract(
      "Today",
      "bestTime",
      "must reference a model_forecast",
    );
  }
}

function validateTodayComparison(todayResponse) {
  const {
    comparison,
    currentObservedAtUtc,
    currentPriceCents,
    priceDifferenceCents,
  } = todayResponse;

  const hasCurrentPrice = currentPriceCents !== null;
  const hasObservationTime = currentObservedAtUtc !== null;

  if (hasCurrentPrice !== hasObservationTime) {
    failContract(
      "Today",
      "currentPriceCents and currentObservedAtUtc",
      "must be present or null together",
    );
  }

  const hasEligibleForecast = (
    todayResponse.futureForecastStatus === "available"
    && todayResponse.bestTime !== null
  );
  const hasComparisonEvidence = (
    hasEligibleForecast && hasCurrentPrice
  );

  if (
    hasComparisonEvidence
    !== (comparison !== "unavailable")
  ) {
    failContract(
      "Today",
      "comparison",
      "must reflect eligible forecast and observed-price evidence",
    );
  }

  if (comparison === "unavailable") {
    if (priceDifferenceCents !== null) {
      failContract(
        "Today",
        "priceDifferenceCents",
        "must be null when comparison is unavailable",
      );
    }

    return;
  }

  if (priceDifferenceCents === null) {
    failContract(
      "Today",
      "priceDifferenceCents",
      `is required when comparison is ${comparison}`,
    );
  }

  if (
    comparison === "forecast_equal"
    && priceDifferenceCents !== 0
  ) {
    failContract(
      "Today",
      "priceDifferenceCents",
      "must equal zero when comparison is forecast_equal",
    );
  }

  if (
    comparison !== "forecast_equal"
    && priceDifferenceCents <= 0
  ) {
    failContract(
      "Today",
      "priceDifferenceCents",
      `must be positive when comparison is ${comparison}`,
    );
  }
}

/**
 * Validates the observed-price response before React receives external data.
 */
export function validateNowApiResponse(payload) {
  const nowResponse = requireObject(payload, "Now", "response");

  requireTimestamp(nowResponse.generatedAt, "Now", "generatedAt");
  requireKnownValue(
    nowResponse.confidence,
    CONFIDENCE_LEVELS,
    "Now",
    "confidence",
  );
  requireBoolean(nowResponse.stale, "Now", "stale");

  const observedPrice = requireObject(nowResponse.price, "Now", "price");
  requireFiniteNumber(observedPrice.value, "Now", "price.value");

  if (observedPrice.unit !== "¢/kWh") {
    failContract("Now", "price.unit", "must equal ¢/kWh");
  }

  if (observedPrice.observedAtUtc !== undefined) {
    requireTimestamp(
      observedPrice.observedAtUtc,
      "Now",
      "price.observedAtUtc",
    );
  }

  const recommendation = requireObject(
    nowResponse.recommendation,
    "Now",
    "recommendation",
  );
  validatePublicRecommendation(
    recommendation.level,
    "Now",
    "recommendation.level",
  );
  requireKnownValue(
    recommendation.explanationKey,
    EXPLANATION_KEYS,
    "Now",
    "recommendation.explanationKey",
  );
  requireKnownValue(
    recommendation.actionKey,
    ACTION_KEYS,
    "Now",
    "recommendation.actionKey",
  );
  requireKnownValue(
    nowResponse.contextKey,
    MARKET_CONTEXT_KEYS,
    "Now",
    "contextKey",
  );

  return nowResponse;
}

/**
 * Validates forecast payload shape without rebuilding server-owned decisions.
 */
export function validateTodayApiResponse(payload) {
  const todayResponse = requireObject(payload, "Today", "response");

  requireTimestamp(todayResponse.generatedAt, "Today", "generatedAt");
  requireKnownValue(
    todayResponse.confidence,
    CONFIDENCE_LEVELS,
    "Today",
    "confidence",
  );
  requireBoolean(todayResponse.stale, "Today", "stale");
  requireKnownValue(
    todayResponse.futureForecastStatus,
    FUTURE_FORECAST_STATES,
    "Today",
    "futureForecastStatus",
  );
  requireKnownValue(
    todayResponse.comparison,
    TODAY_COMPARISON_STATES,
    "Today",
    "comparison",
  );
  requireNullableFiniteNumber(
    todayResponse.currentPriceCents,
    "Today",
    "currentPriceCents",
  );
  requireNullableTimestamp(
    todayResponse.currentObservedAtUtc,
    "Today",
    "currentObservedAtUtc",
  );
  requireNullableFiniteNumber(
    todayResponse.priceDifferenceCents,
    "Today",
    "priceDifferenceCents",
  );
  validateTodayComparison(todayResponse);

  if (!Array.isArray(todayResponse.forecasts)) {
    failContract("Today", "forecasts", "must be an array");
  }

  if (
    todayResponse.forecasts.length
    !== SUPPORTED_FORECAST_HORIZONS_HOURS.length
  ) {
    failContract(
      "Today",
      "forecasts",
      "must contain exactly five horizon points",
    );
  }

  const forecasts = todayResponse.forecasts.map(validateTodayForecast);
  const forecastHorizons = forecasts.map(
    (forecast) => forecast.horizonHours,
  );

  const hasExpectedHorizons = SUPPORTED_FORECAST_HORIZONS_HOURS.every(
    (horizonHours, index) => forecastHorizons[index] === horizonHours,
  );

  if (!hasExpectedHorizons) {
    failContract(
      "Today",
      "forecasts[].horizonHours",
      "must equal 1, 3, 6, 12, and 24 in order",
    );
  }

  validateBestTime(todayResponse.bestTime, forecasts);

  if (
    todayResponse.futureForecastStatus === "available"
    && todayResponse.bestTime === null
  ) {
    failContract(
      "Today",
      "bestTime",
      "is required when futureForecastStatus is available",
    );
  }

  if (
    todayResponse.futureForecastStatus !== "available"
    && todayResponse.bestTime !== null
  ) {
    failContract(
      "Today",
      "bestTime",
      "must be null when no eligible future model forecast is available",
    );
  }

  return todayResponse;
}

export function getPublicApiErrorMessage(payload) {
  if (payload === null || typeof payload !== "object") {
    return null;
  }

  if (typeof payload.error === "string" && payload.error.trim() !== "") {
    return payload.error;
  }

  if (
    payload.error !== null
    && typeof payload.error === "object"
    && typeof payload.error.message === "string"
    && payload.error.message.trim() !== ""
  ) {
    return payload.error.message;
  }

  return null;
}
