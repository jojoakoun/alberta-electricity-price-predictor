const {
  createAnalyticsEvent,
} = require("../repositories/analytics-repository");

const ALLOWED_EVENTS = new Set([
  "page_view",
  "refresh",
]);

const ALLOWED_PAGES = new Set([
  "now",
  "today",
  "learn",
  "project",
]);

class AnalyticsValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "AnalyticsValidationError";
  }
}

function normalizeAnalyticsEvent(payload = {}) {
  const eventType = String(
    payload.eventType ?? "",
  ).trim();

  const page = String(
    payload.page ?? "",
  ).trim();

  const sessionId = String(
    payload.sessionId ?? "",
  ).trim();

  const appVersionValue = String(
    payload.appVersion ?? "",
  ).trim();

  if (!ALLOWED_EVENTS.has(eventType)) {
    throw new AnalyticsValidationError(
      "Unsupported analytics event type.",
    );
  }

  if (!ALLOWED_PAGES.has(page)) {
    throw new AnalyticsValidationError(
      "Unsupported analytics page.",
    );
  }

  if (
    sessionId.length < 16
    || sessionId.length > 128
    || !/^[A-Za-z0-9_-]+$/.test(sessionId)
  ) {
    throw new AnalyticsValidationError(
      "Invalid anonymous session identifier.",
    );
  }

  if (appVersionValue.length > 80) {
    throw new AnalyticsValidationError(
      "App version is too long.",
    );
  }

  return {
    eventType,
    page,
    sessionId,
    appVersion: appVersionValue || null,
  };
}

async function recordAnalyticsEvent(payload) {
  const event = normalizeAnalyticsEvent(payload);

  return createAnalyticsEvent(event);
}

module.exports = {
  AnalyticsValidationError,
  normalizeAnalyticsEvent,
  recordAnalyticsEvent,
};
