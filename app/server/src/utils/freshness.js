const HIGH_CONFIDENCE_MAX_MINUTES = 75;
const MODERATE_CONFIDENCE_MAX_MINUTES = 150;

function getFreshness(generatedAt, now = new Date()) {
  const generatedDate = new Date(generatedAt);
  const currentDate = new Date(now);

  if (
    Number.isNaN(generatedDate.getTime()) ||
    Number.isNaN(currentDate.getTime())
  ) {
    throw new TypeError("Freshness requires valid dates.");
  }

  const ageMinutes =
    (currentDate.getTime() - generatedDate.getTime()) / (60 * 1000);

  if (ageMinutes < 0) {
    throw new RangeError("generatedAt cannot be in the future.");
  }

  if (ageMinutes <= HIGH_CONFIDENCE_MAX_MINUTES) {
    return {
      confidence: "high",
      stale: false,
    };
  }

  if (ageMinutes <= MODERATE_CONFIDENCE_MAX_MINUTES) {
    return {
      confidence: "moderate",
      stale: true,
    };
  }

  return {
    confidence: "low",
    stale: true,
  };
}

module.exports = {
  getFreshness,
};
