import {
  useEffect,
  useRef,
  useState,
} from "react";

export function useInView({
  rootMargin = "0px 0px -10% 0px",
  threshold = 0.2,
} = {}) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;

    if (!node) {
      return;
    }

    if (
      typeof window === "undefined"
      || !("IntersectionObserver" in window)
    ) {
      setInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) {
          return;
        }

        setInView(true);
        observer.disconnect();
      },
      {
        rootMargin,
        threshold,
      },
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, [
    rootMargin,
    threshold,
  ]);

  return {
    ref,
    inView,
  };
}
