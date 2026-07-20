import type {
  CSSProperties,
  ReactNode,
} from "react";

import { useInView } from "./useInView";

type AppRevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
};

export function AppReveal({
  children,
  className = "",
  delay = 0,
}: AppRevealProps) {
  const {
    ref,
    inView,
  } = useInView<HTMLDivElement>({
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
      } as CSSProperties}
    >
      {children}
    </div>
  );
}
