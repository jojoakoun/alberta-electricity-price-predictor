const { ALBERTA_TIME_ZONE, formatAlbertaTime } = require("./time");

const MINUTES_PER_HOUR = 60;
const MILLISECONDS_PER_MINUTE = 60 * 1000;

function getAlbertaHour(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    throw new TypeError("A valid target timestamp is required.");
  }

  const hourPart = new Intl.DateTimeFormat("en-CA", {
    timeZone: ALBERTA_TIME_ZONE,
    hour: "numeric",
    hourCycle: "h23",
  })
    .formatToParts(date)
    .find((part) => part.type === "hour");

  return Number(hourPart.value);
}

function getTemporalWordingKey(targetTime, viewedAt = new Date()) {
  const targetDate = new Date(targetTime);
  const viewedDate = new Date(viewedAt);

  if (
    Number.isNaN(targetDate.getTime()) ||
    Number.isNaN(viewedDate.getTime())
  ) {
    throw new TypeError("Temporal wording requires valid timestamps.");
  }

  const differenceMinutes =
    (targetDate.getTime() - viewedDate.getTime()) /
    MILLISECONDS_PER_MINUTE;

  if (differenceMinutes < 0) {
    throw new RangeError("Target time cannot be before the viewing time.");
  }

  if (differenceMinutes <= 90) {
    return "very_soon";
  }

  if (differenceMinutes <= 4 * MINUTES_PER_HOUR) {
    return "in_a_few_hours";
  }

  // Check the long horizon before local dayparts.
  if (differenceMinutes >= 20 * MINUTES_PER_HOUR) {
    return "tomorrow_around_this_time";
  }

  const localHour = getAlbertaHour(targetDate);

  if (localHour >= 12 && localHour <= 17) {
    return "this_afternoon";
  }

  if (localHour >= 18 && localHour <= 22) {
    return "this_evening";
  }

  if (localHour >= 23 || localHour <= 5) {
    return "overnight";
  }

  // The specification does not name the 6:00–11:59 fallback case.
  return "later_today";
}

function buildForecastTime(targetTime, viewedAt = new Date()) {
  const targetDate = new Date(targetTime);

  if (Number.isNaN(targetDate.getTime())) {
    throw new TypeError("A valid target timestamp is required.");
  }

  return {
    targetTimeUtc: targetDate.toISOString(),
    targetTimeLocal: formatAlbertaTime(targetDate),
    temporalWordingKey: getTemporalWordingKey(targetDate, viewedAt),
  };
}

module.exports = {
  buildForecastTime,
  getTemporalWordingKey,
};
