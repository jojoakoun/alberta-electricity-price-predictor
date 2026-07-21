import { getLanguage } from "./language";

const locales = {
  en: "en-CA",
  fr: "fr-CA",
};

const ALBERTA_TIME_ZONE = "America/Edmonton";

export function formatNumber(
  value,
  minimumFractionDigits = 2,
  maximumFractionDigits =
    minimumFractionDigits,
) {
  return new Intl.NumberFormat(
    locales[getLanguage()],
    {
      minimumFractionDigits,
      maximumFractionDigits,
    },
  ).format(value);
}

export function formatAlbertaTime(
  isoDate,
) {
  const date = new Date(isoDate);

  if (Number.isNaN(date.getTime())) {
    return isoDate;
  }

  const language = getLanguage();

  return new Intl.DateTimeFormat(
    locales[language],
    {
      hour: "numeric",
      minute: "2-digit",
      hour12: language === "en",
      timeZone: ALBERTA_TIME_ZONE,
    },
  ).format(date);
}

function getAlbertaDateParts(isoDate) {
  const date = new Date(isoDate);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  function getNumericPart(partName) {
    return Number(
      new Intl.DateTimeFormat(
        "en-CA",
        {
          [partName]: "numeric",
          timeZone: ALBERTA_TIME_ZONE,
        },
      ).format(date),
    );
  }

  return {
    year: getNumericPart("year"),
    month: getNumericPart("month"),
    day: getNumericPart("day"),
  };
}

function localDateNumber(parts) {
  return Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
  );
}

/**
 * Compare Alberta calendar dates rather than UTC dates when choosing a day label.
 */
export function formatAlbertaDay(isoDate, referenceIsoDate) {
  const targetParts =
    getAlbertaDateParts(isoDate);

  const referenceParts =
    getAlbertaDateParts(referenceIsoDate);

  if (!targetParts || !referenceParts) {
    return "";
  }

  const differenceDays = Math.round(
    (
      localDateNumber(targetParts)
      - localDateNumber(referenceParts)
    ) / 86400000,
  );

  const language = getLanguage();

  if (differenceDays === 0) {
    return language === "fr"
      ? "Aujourd’hui"
      : "Today";
  }

  if (differenceDays === 1) {
    return language === "fr"
      ? "Demain"
      : "Tomorrow";
  }

  return new Intl.DateTimeFormat(
    locales[language],
    {
      weekday: "short",
      timeZone: ALBERTA_TIME_ZONE,
    },
  ).format(new Date(isoDate));
}
