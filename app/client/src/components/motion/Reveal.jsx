import { useInView } from "./useInView";

export function Reveal({
  children,
  className = "",
  delay = 0,
  threshold = 0.08,
}) {
  const {
    ref,
    inView,
  } = useInView({
    rootMargin: "0px 0px -4% 0px",
    threshold,
  });

  return (
    <div
      ref={ref}
      className={[
        "project-reveal",
        inView ? "is-visible" : "",
        className,
      ].join(" ")}
      style={{
        "--motion-delay": `${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}
