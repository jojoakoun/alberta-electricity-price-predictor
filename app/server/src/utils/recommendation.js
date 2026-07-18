const RECOMMENDATION_LEVELS = Object.freeze({
  Recommended: "recommended",
  Acceptable: "acceptable",
  Avoid: "avoid",
});

function normalizeRecommendation(value) {
  const recommendation = RECOMMENDATION_LEVELS[value];

  if (!recommendation) {
    throw new Error(`Unsupported recommendation: ${value}`);
  }

  return recommendation;
}

module.exports = {
  normalizeRecommendation,
};
