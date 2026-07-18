import type {
  ComponentPropsWithoutRef,
  ElementType,
  ReactNode,
} from "react";

type CardProps<TElement extends ElementType = "section"> = {
  as?: TElement;
  children: ReactNode;
  className?: string;
} & Omit<
  ComponentPropsWithoutRef<TElement>,
  "as" | "children" | "className"
>;

export function Card<TElement extends ElementType = "section">({
  as,
  children,
  className = "",
  ...props
}: CardProps<TElement>) {
  const Component = as ?? "section";

  return (
    <Component
      className={[
        "rounded-[var(--radius)]",
        "border border-[var(--color-border)]",
        "bg-[var(--color-surface)]",
        "p-[var(--space-4)]",
        "shadow-[var(--shadow-card)]",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </Component>
  );
}
