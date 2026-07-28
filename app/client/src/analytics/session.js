const ANALYTICS_SESSION_KEY =
  "wattwise_analytics_session_id";

/**
 * Return one anonymous browser identifier.
 *
 * This identifier contains no name, email, IP address,
 * location, or browser fingerprint.
 */
export function getAnalyticsSessionId() {
  try {
    const existingSessionId = window.localStorage.getItem(
      ANALYTICS_SESSION_KEY,
    );

    if (existingSessionId) {
      return existingSessionId;
    }

    const sessionId =
      window.crypto?.randomUUID?.()
      ?? [
        "anonymous",
        Date.now(),
        Math.random().toString(36).slice(2),
      ].join("_");

    window.localStorage.setItem(
      ANALYTICS_SESSION_KEY,
      sessionId,
    );

    return sessionId;
  } catch {
    // Storage may be unavailable in privacy-restricted browsers.
    return [
      "temporary",
      Date.now(),
      Math.random().toString(36).slice(2),
    ].join("_");
  }
}
