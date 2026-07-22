const TIMESTAMP_WITH_TIMEZONE_PATTERN = (
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$/
);

export const CONFIDENCE_LEVELS = new Set([
  "high",
  "moderate",
  "low",
]);

export const RECOMMENDATION_LEVELS = new Set([
  "recommended",
  "acceptable",
  "avoid",
]);

export const EXPLANATION_KEYS = new Set([
  "lower_than_usual",
  "about_average",
  "acceptable_market_risk",
  "higher_than_usual",
]);

export function failContract(contractName, fieldPath, expectation) {
  throw new TypeError(
    `Invalid ${contractName} API response: ${fieldPath} ${expectation}.`,
  );
}

export function requireObject(value, contractName, fieldPath) {
  if (
    value === null
    || typeof value !== "object"
    || Array.isArray(value)
  ) {
    failContract(contractName, fieldPath, "must be an object");
  }

  return value;
}

export function requireBoolean(value, contractName, fieldPath) {
  if (typeof value !== "boolean") {
    failContract(contractName, fieldPath, "must be a boolean");
  }
}

export function requireFiniteNumber(value, contractName, fieldPath) {
  if (!Number.isFinite(value)) {
    failContract(contractName, fieldPath, "must be a finite number");
  }
}

export function requireNonEmptyString(value, contractName, fieldPath) {
  if (typeof value !== "string" || value.trim() === "") {
    failContract(contractName, fieldPath, "must be a non-empty string");
  }
}

export function requireTimestamp(value, contractName, fieldPath) {
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

export function requireKnownValue(
  value,
  allowedValues,
  contractName,
  fieldPath,
) {
  if (!allowedValues.has(value)) {
    failContract(contractName, fieldPath, "contains an unsupported value");
  }
}

export function requireNullableFiniteNumber(
  value,
  contractName,
  fieldPath,
) {
  if (value !== null) {
    requireFiniteNumber(value, contractName, fieldPath);
  }
}

export function requireNullableTimestamp(value, contractName, fieldPath) {
  if (value !== null) {
    requireTimestamp(value, contractName, fieldPath);
  }
}

export function validatePublicRecommendation(
  value,
  contractName,
  fieldPath,
) {
  requireKnownValue(
    value,
    RECOMMENDATION_LEVELS,
    contractName,
    fieldPath,
  );
}
