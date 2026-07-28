import {
  useEffect,
} from "react";

import {
  trackPageView,
} from "./analytics";

/**
 * Record one anonymous page view when a product page mounts.
 */
export function usePageAnalytics(page) {
  useEffect(() => {
    trackPageView(page);
  }, [page]);
}
