const RECOMMENDATION_COLORS = Object.freeze({
  recommended: "var(--color-brand)",
  acceptable: "var(--color-okay)",
  avoid: "var(--color-wait)",
});

/**
 * Return the visual color associated with a forecast recommendation.
 *
 * The halo identifies the best available horizon. The point color
 * always communicates Good, Okay, or Better to wait.
 */
export function getRecommendationColor(recommendation) {
  return (
    RECOMMENDATION_COLORS[recommendation]
    ?? "var(--color-text)"
  );
}
