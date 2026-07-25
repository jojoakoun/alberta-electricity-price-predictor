export const supportedLanguages = Object.freeze([
  "en",
  "fr",
]);

const STORAGE_KEY = "wattwise-language";

const pageTitles = {
  en: "WattWise — Smarter Electricity Decisions",
  fr: "WattWise — Des décisions plus intelligentes",
};

function detectLanguage() {
  if (typeof window === "undefined") {
    return "en";
  }

  try {
    const storedLanguage =
      window.localStorage.getItem(STORAGE_KEY);

    if (supportedLanguages.includes(storedLanguage)) {
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

const listeners = new Set();

export function getLanguage() {
  return currentLanguage;
}

export function getServerLanguage() {
  return "en";
}

export function subscribeLanguage(
  listener,
) {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

export function applyLanguage(
  language,
) {
  if (typeof document === "undefined") {
    return;
  }

  document.documentElement.lang = language;
  document.title = pageTitles[language];
}

export function setLanguage(
  language,
) {
  if (!supportedLanguages.includes(language)) {
    throw new TypeError(`Unsupported language: ${language}.`);
  }

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
