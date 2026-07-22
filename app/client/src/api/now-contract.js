import {
  CONFIDENCE_LEVELS,
  EXPLANATION_KEYS,
  failContract,
  requireBoolean,
  requireFiniteNumber,
  requireKnownValue,
  requireObject,
  requireTimestamp,
  validatePublicRecommendation,
} from "./contract-validators";

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
