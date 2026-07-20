import { en } from "./i18n/en";
import { fr } from "./i18n/fr";
import {
  getLanguage,
  type Language,
} from "./i18n/language";

type WidenCopy<T> =
  T extends string
    ? string
    : T extends readonly (infer TItem)[]
      ? readonly WidenCopy<TItem>[]
      : T extends object
        ? {
            readonly [TKey in keyof T]:
              WidenCopy<T[TKey]>;
          }
        : T;

export type Copy = WidenCopy<typeof en>;

const translations: Record<
  Language,
  Copy
> = {
  en,
  fr,
};

export const copy = new Proxy(
  {} as Copy,
  {
    get(_target, property) {
      return translations[getLanguage()][
        property as keyof Copy
      ];
    },
  },
);
