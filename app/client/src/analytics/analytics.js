import {
  getAnalyticsSessionId,
} from "./session";

const ANALYTICS_ENDPOINT =
  "/api/v1/analytics/events";

const APP_VERSION =
  import.meta.env.VITE_APP_VERSION
  || "development";

const PAGE_VIEW_DEDUPLICATION_MS = 1_000;

let lastPageView = {
  page: null,
  recordedAt: 0,
};

/**
 * Send anonymous usage information without interrupting
 * the product experience when analytics is unavailable.
 */
export async function trackAnalyticsEvent(
  eventType,
  page,
) {
  try {
    await fetch(
      ANALYTICS_ENDPOINT,
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          eventType,
          page,
          sessionId: getAnalyticsSessionId(),
          appVersion: APP_VERSION,
        }),
        keepalive: true,
      },
    );
  } catch {
    // Analytics must never block or break WattWise.
  }
}

export function trackPageView(page) {
  const recordedAt = Date.now();

  // React development checks can mount a component twice.
  // Suppress only the immediate duplicate, not later revisits.
  if (
    lastPageView.page === page
    && (
      recordedAt - lastPageView.recordedAt
      < PAGE_VIEW_DEDUPLICATION_MS
    )
  ) {
    return;
  }

  lastPageView = {
    page,
    recordedAt,
  };

  void trackAnalyticsEvent(
    "page_view",
    page,
  );
}

export function trackRefresh(page) {
  void trackAnalyticsEvent(
    "refresh",
    page,
  );
}
