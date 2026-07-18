import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = {
  children: ReactNode;
  variant?: ButtonVariant;
} & ButtonHTMLAttributes<HTMLButtonElement>;

const variantClasses: Record<ButtonVariant, string> = {
  primary: [
    "bg-[var(--color-brand)]",
    "text-[var(--color-surface)]",
    "hover:opacity-90",
  ].join(" "),

  secondary: [
    "border border-[var(--color-brand)]",
    "bg-[var(--color-surface)]",
    "text-[var(--color-brand)]",
    "hover:bg-[var(--color-brand-surface)]",
  ].join(" "),

  ghost: [
    "bg-transparent",
    "text-[var(--color-brand)]",
    "hover:bg-[var(--color-brand-surface)]",
  ].join(" "),
};

export function Button({
  children,
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={[
        "inline-flex min-h-11 items-center justify-center",
        "rounded-[var(--radius)]",
        "px-[var(--space-3)] py-[var(--space-2)]",
        "font-medium",
        "transition-[opacity,background-color,color]",
        "duration-[var(--motion-duration)]",
        "ease-[var(--motion-easing)]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variantClasses[variant],
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
