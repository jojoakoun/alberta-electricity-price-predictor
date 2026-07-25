import { useInView } from "./useInView";

export function AppReveal({
  children,
  className = "",
  delay = 0,
}) {
  const {
    ref,
    inView,
  } = useInView({
    rootMargin: "0px 0px -4% 0px",
    threshold: 0.08,
  });

  return (
    <div
      ref={ref}
      className={[
        "app-reveal",
        inView ? "is-visible" : "",
        className,
      ].join(" ")}
      style={{
        "--app-delay": `${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}
