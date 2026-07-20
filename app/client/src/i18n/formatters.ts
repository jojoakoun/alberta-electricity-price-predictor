import { getLanguage } from "./language";

const locales = {
  en: "en-CA",
  fr: "fr-CA",
} as const;

const ALBERTA_TIME_ZONE = "America/Edmonton";

type LocalDateParts = {
  year: number;
  month: number;
  day: number;
};

export function formatNumber(
  value: number,
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
  isoDate: string,
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

function getAlbertaDateParts(
  isoDate: string,
): LocalDateParts | null {
  const date = new Date(isoDate);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  const parts = new Intl.DateTimeFormat(
    "en-CA",
    {
      year: "numeric",
      month: "numeric",
      day: "numeric",
      timeZone: ALBERTA_TIME_ZONE,
    },
  ).formatToParts(date);

  const values = Object.fromEntries(
    parts.map((part) => [
      part.type,
      part.value,
    ]),
  );

  return {
    year: Number(values.year),
    month: Number(values.month),
    day: Number(values.day),
  };
}

function localDateNumber(
  parts: LocalDateParts,
) {
  return Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
  );
}

export function formatAlbertaDay(
  isoDate: string,
  referenceIsoDate: string,
) {
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
    ) / 86_400_000,
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
