import { en } from "./i18n/en";
import { fr } from "./i18n/fr";
import { getLanguage } from "./i18n/language";

const translations = {
  en,
  fr,
};

// Resolve copy at access time so a language change updates every consumer
// without threading translation objects through the component tree.
export const copy = new Proxy(
  {},
  {
    get(_target, property) {
      return translations[getLanguage()][property];
    },
  },
);
