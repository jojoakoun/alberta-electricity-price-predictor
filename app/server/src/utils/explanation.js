const EXPLANATION_KEYS = Object.freeze({
  "Predicted price is favorable compared with the recent market.":
    "lower_than_usual",
  "Predicted price is acceptable but market risk is increasing.":
    "acceptable_market_risk",
  "Predicted price is high compared with the recent market.":
    "higher_than_usual",
});

function getExplanationKey(value) {
  const explanationKey = EXPLANATION_KEYS[value];

  if (!explanationKey) {
    throw new Error("Unsupported persisted explanation.");
  }

  return explanationKey;
}

module.exports = {
  getExplanationKey,
};
