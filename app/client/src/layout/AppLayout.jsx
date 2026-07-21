import {
  BookOpen,
  Clock3,
  Folder,
  House,
  Menu,
  X,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  NavLink,
  Outlet,
} from "react-router";

import { copy } from "../copy";
import {
  getLanguage,
  setLanguage,
} from "../i18n/language";

const navigation = [
  {
    to: "/",
    label: () => copy.navigation.now,
    Icon: House,
  },
  {
    to: "/today",
    label: () => copy.navigation.today,
    Icon: Clock3,
  },
  {
    to: "/learn",
    label: () => copy.navigation.learn,
    Icon: BookOpen,
  },
  {
    to: "/project",
    label: () => copy.navigation.project,
    Icon: Folder,
  },
];

function linkClassName({ isActive }) {
  return [
    "inline-flex min-h-11 items-center",
    "gap-[var(--space-2)]",
    "rounded-[var(--radius)]",
    "px-[var(--space-3)]",
    isActive
      ? "bg-[var(--color-brand-surface)] font-semibold text-[var(--color-brand)]"
      : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]",
  ].join(" ");
}

function languageButtonClass(language) {
  const activeLanguage = getLanguage();

  return [
    "inline-flex min-h-9 items-center",
    "justify-center gap-1.5",
    "rounded-[calc(var(--radius)-0.2rem)]",
    "px-2.5 text-sm font-semibold",
    "transition-colors",
    language === activeLanguage
      ? "bg-[var(--color-brand)] text-white"
      : "text-[var(--color-text-muted)] hover:bg-[var(--color-brand-surface)]",
  ].join(" ");
}

function LanguageSelector() {
  return (
    <div
      aria-label={copy.language.selector}
      className={[
        "inline-flex items-center gap-1",
        "rounded-[var(--radius)]",
        "border border-[var(--color-border)]",
        "bg-[var(--color-surface)]",
        "p-1",
      ].join(" ")}
      role="group"
    >
      <button
        aria-label={copy.language.english}
        aria-pressed={getLanguage() === "en"}
        className={languageButtonClass("en")}
        onClick={() => setLanguage("en")}
        type="button"
      >
        <span aria-hidden="true">🇬🇧</span>
        EN
      </button>

      <button
        aria-label={copy.language.french}
        aria-pressed={getLanguage() === "fr"}
        className={languageButtonClass("fr")}
        onClick={() => setLanguage("fr")}
        type="button"
      >
        <span aria-hidden="true">🇫🇷</span>
        FR
      </button>
    </div>
  );
}

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-bg)]">
      <header
        className={[
          "sticky top-0 z-40",
          "border-b border-[var(--color-border)]",
          "bg-[var(--color-surface)]",
        ].join(" ")}
      >
        <div
          className={[
            "mx-auto flex max-w-5xl",
            "items-center justify-between",
            "gap-[var(--space-3)]",
            "px-[var(--space-3)] py-[var(--space-2)]",
            "lg:px-[var(--space-5)]",
          ].join(" ")}
        >
          <NavLink
            to="/"
            className={[
              "group inline-flex min-h-11",
              "items-center",
              "text-[var(--font-size-h2)]",
              "font-semibold text-[var(--color-brand)]",
            ].join(" ")}
          >
            <img
              alt=""
              aria-hidden="true"
              className={[
                "mr-[var(--space-2)]",
                "h-8 w-8 shrink-0",
                "transition-transform",
                "group-hover:scale-105",
              ].join(" ")}
              height="32"
              src="/wattwise-mark.svg"
              width="32"
            />

            <span>{copy.brand.name}</span>
          </NavLink>

          <div className="hidden items-center gap-2 md:flex">
            <nav
              aria-label={copy.language.mainNavigation}
              className="flex items-center gap-1"
            >
              {navigation.map(
                ({
                  to,
                  label,
                }) => (
                  <NavLink
                    key={to}
                    className={linkClassName}
                    end={to === "/"}
                    to={to}
                  >
                    {label()}
                  </NavLink>
                ),
              )}
            </nav>

            <LanguageSelector />
          </div>

          <button
            aria-controls="mobile-menu"
            aria-expanded={menuOpen}
            aria-label={
              menuOpen
                ? copy.language.closeMenu
                : copy.language.openMenu
            }
            className={[
              "inline-flex min-h-11 min-w-11",
              "items-center justify-center",
              "rounded-[var(--radius)]",
              "text-[var(--color-text)]",
              "hover:bg-[var(--color-brand-surface)]",
              "md:hidden",
            ].join(" ")}
            onClick={() =>
              setMenuOpen((current) => !current)
            }
            type="button"
          >
            {menuOpen ? (
              <X aria-hidden="true" size={24} />
            ) : (
              <Menu aria-hidden="true" size={24} />
            )}
          </button>
        </div>

        {menuOpen && (
          <nav
            id="mobile-menu"
            aria-label={copy.language.mobileNavigation}
            className={[
              "absolute inset-x-0 top-full",
              "border-b border-[var(--color-border)]",
              "bg-[var(--color-surface)]",
              "p-[var(--space-3)]",
              "shadow-[var(--shadow-card)]",
              "md:hidden",
            ].join(" ")}
          >
            <div className="mx-auto grid max-w-5xl gap-2">
              {navigation.map(
                ({
                  to,
                  label,
                  Icon,
                }) => (
                  <NavLink
                    key={to}
                    className={linkClassName}
                    end={to === "/"}
                    onClick={() => setMenuOpen(false)}
                    to={to}
                  >
                    <Icon
                      aria-hidden="true"
                      size={20}
                    />

                    {label()}
                  </NavLink>
                ),
              )}

              <div
                className={[
                  "mt-2 flex items-center",
                  "justify-between gap-3",
                  "border-t border-[var(--color-border)]",
                  "pt-3",
                ].join(" ")}
              >
                <span className="font-semibold">
                  {copy.language.selector}
                </span>

                <LanguageSelector />
              </div>
            </div>
          </nav>
        )}
      </header>

      <main
        className={[
          "mx-auto w-full max-w-5xl flex-1",
          "px-[var(--space-3)] py-[var(--space-5)]",
          "lg:px-[var(--space-5)]",
        ].join(" ")}
      >
        <Outlet />
      </main>
    </div>
  );
}
