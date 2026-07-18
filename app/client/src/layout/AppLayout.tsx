import { BookOpen, Clock3, House } from "lucide-react";
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

function navigationClassName({
  isActive,
}: {
  isActive: boolean;
}) {
  return [
    "relative inline-flex min-h-11 items-center justify-center",
    "gap-[var(--space-1)]",
    "px-[var(--space-2)]",
    "text-[var(--color-text-muted)]",
    "transition-colors",
    "duration-[var(--motion-duration)]",
    "ease-[var(--motion-easing)]",
    "after:absolute after:inset-x-[var(--space-2)] after:bottom-0",
    "after:h-0.5 after:bg-transparent",
    isActive
      ? "font-semibold text-[var(--color-text)] after:bg-[var(--color-brand)]"
      : "hover:text-[var(--color-text)]",
  ].join(" ");
}

export function AppLayout() {
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <header
        className={[
          "border-b border-[var(--color-border)]",
          "bg-[var(--color-surface)]",
        ].join(" ")}
      >
        <div
          className={[
            "mx-auto flex max-w-5xl items-center justify-between",
            "px-[var(--space-3)] py-[var(--space-2)]",
            "md:px-[var(--space-5)]",
          ].join(" ")}
        >
          <NavLink
            to="/"
            className={[
              "inline-flex min-h-11 items-center",
              "text-[var(--color-brand)]",
              "text-[var(--font-size-h2)] font-semibold",
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
                to={to}
                end={to === "/"}
                className={navigationClassName}
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main
        className={[
          "mx-auto w-full max-w-3xl",
          "px-[var(--space-3)]",
          "py-[var(--space-5)]",
          "pb-[calc(var(--space-7)+var(--space-5))]",
          "md:px-[var(--space-5)] md:pb-[var(--space-6)]",
        ].join(" ")}
      >
        <Outlet />
      </main>

      <nav
        aria-label="Mobile navigation"
        className={[
          "fixed inset-x-0 bottom-0 z-20",
          "grid grid-cols-3",
          "border-t border-[var(--color-border)]",
          "bg-[var(--color-surface)]",
          "md:hidden",
        ].join(" ")}
      >
        {navigation.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={navigationClassName}
          >
            <Icon aria-hidden="true" size={20} strokeWidth={2} />
            <span className="text-[var(--font-size-caption)]">
              {label}
            </span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
