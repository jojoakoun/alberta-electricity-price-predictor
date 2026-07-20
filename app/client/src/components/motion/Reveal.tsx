import type {
  CSSProperties,
  ReactNode,
} from "react";

import { useInView } from "./useInView";

type RevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
  threshold?: number;
};

export function Reveal({
  children,
  className = "",
  delay = 0,
  threshold = 0.08,
}: RevealProps) {
  const {
    ref,
    inView,
  } = useInView<HTMLDivElement>({
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
      } as CSSProperties}
    >
      {children}
    </div>
  );
}
