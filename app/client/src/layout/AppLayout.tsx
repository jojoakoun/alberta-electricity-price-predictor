import {
  BookOpen,
  Clock3,
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

const navigation = [
  {
    to: "/",
    label: copy.navigation.now,
    Icon: House,
  },
  {
    to: "/today",
    label: copy.navigation.today,
    Icon: Clock3,
  },
  {
    to: "/learn",
    label: copy.navigation.learn,
    Icon: BookOpen,
  },
] as const;

function linkClassName({
  isActive,
}: {
  isActive: boolean;
}) {
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
            "px-[var(--space-3)] py-[var(--space-2)]",
            "lg:px-[var(--space-5)]",
          ].join(" ")}
        >
          <NavLink
            to="/"
            className={[
              "inline-flex min-h-11 items-center",
              "text-[var(--font-size-h2)]",
              "font-semibold text-[var(--color-brand)]",
            ].join(" ")}
          >
            {copy.brand.name}
          </NavLink>

          <nav
            aria-label="Main navigation"
            className="hidden items-center gap-[var(--space-2)] md:flex"
          >
            {navigation.map(({ to, label }) => (
              <NavLink
                key={to}
                className={linkClassName}
                end={to === "/"}
                to={to}
              >
                {label}
              </NavLink>
            ))}
          </nav>

          <button
            aria-controls="mobile-menu"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            className={[
              "inline-flex min-h-11 min-w-11",
              "items-center justify-center",
              "rounded-[var(--radius)]",
              "text-[var(--color-text)]",
              "hover:bg-[var(--color-brand-surface)]",
              "md:hidden",
            ].join(" ")}
            onClick={() => setMenuOpen((current) => !current)}
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
            aria-label="Mobile navigation"
            className={[
              "absolute inset-x-0 top-full",
              "border-b border-[var(--color-border)]",
              "bg-[var(--color-surface)]",
              "p-[var(--space-3)]",
              "shadow-[var(--shadow-card)]",
              "md:hidden",
            ].join(" ")}
          >
            <div className="mx-auto grid max-w-5xl gap-[var(--space-2)]">
              {navigation.map(({ to, label, Icon }) => (
                <NavLink
                  key={to}
                  className={linkClassName}
                  end={to === "/"}
                  onClick={() => setMenuOpen(false)}
                  to={to}
                >
                  <Icon aria-hidden="true" size={20} />
                  {label}
                </NavLink>
              ))}
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
