export function Card({
  as,
  children,
  className = "",
  ...props
}) {
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
