export const supportedLanguages = [
  "en",
  "fr",
] as const;

export type Language =
  (typeof supportedLanguages)[number];

const STORAGE_KEY = "wattwise-language";

const pageTitles: Record<Language, string> = {
  en: "WattWise — Smarter Electricity Decisions",
  fr: "WattWise — Des décisions plus intelligentes",
};

function detectLanguage(): Language {
  if (typeof window === "undefined") {
    return "en";
  }

  try {
    const storedLanguage =
      window.localStorage.getItem(STORAGE_KEY);

    if (
      storedLanguage === "en"
      || storedLanguage === "fr"
    ) {
      return storedLanguage;
    }
  } catch {
    // Storage can be unavailable in private environments.
  }

  return window.navigator.language
    .toLowerCase()
    .startsWith("fr")
    ? "fr"
    : "en";
}

let currentLanguage = detectLanguage();

const listeners = new Set<() => void>();

export function getLanguage(): Language {
  return currentLanguage;
}

export function getServerLanguage(): Language {
  return "en";
}

export function subscribeLanguage(
  listener: () => void,
) {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

export function applyLanguage(
  language: Language,
) {
  if (typeof document === "undefined") {
    return;
  }

  document.documentElement.lang = language;
  document.title = pageTitles[language];
}

export function setLanguage(
  language: Language,
) {
  currentLanguage = language;

  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      language,
    );
  } catch {
    // The language still changes for the current session.
  }

  applyLanguage(language);

  listeners.forEach((listener) => listener());
}
