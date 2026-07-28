const {
  getAnalyticsSummary,
} = require("../repositories/analytics-repository");

const EMPTY_PAGE_COUNTS = {
  now: 0,
  today: 0,
  learn: 0,
  project: 0,
};

const EMPTY_EVENT_COUNTS = {
  page_view: 0,
  refresh: 0,
};

async function getPrivateAnalytics() {
  const summary = await getAnalyticsSummary();

  const pages = {
    ...EMPTY_PAGE_COUNTS,
  };

  for (const row of summary.pages) {
    pages[row.page] = Number(row.visit_count);
  }

  const events = {
    ...EMPTY_EVENT_COUNTS,
  };

  for (const row of summary.events) {
    events[row.event_type] = Number(row.event_count);
  }

  return {
    totalVisits: Number(
      summary.overview.total_visits,
    ),
    uniqueSessions: Number(
      summary.overview.unique_sessions,
    ),
    todayVisits: Number(
      summary.overview.today_visits,
    ),
    returningSessionsToday: Number(
      summary.returningSessionsToday,
    ),
    pages,
    events,
    hourlyDistribution:
      summary.hourlyDistribution.map((row) => ({
        hourUtc: Number(row.hour_utc),
        visits: Number(row.visit_count),
      })),
    lastVisitUtc:
      summary.overview.last_visit_utc ?? null,
    latestPredictionRunUtc:
      summary.latestPredictionRunUtc,
  };
}

module.exports = {
  getPrivateAnalytics,
};
