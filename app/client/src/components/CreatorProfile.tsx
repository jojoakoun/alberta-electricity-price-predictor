import { copy } from "../copy";

export function CreatorProfile() {
  const creator = copy.creator;

  return (
    <div
      className={[
        "flex flex-wrap items-center",
        "justify-center gap-[var(--space-2)]",
        "text-[var(--font-size-caption)]",
        "text-[var(--color-text-muted)]",
      ].join(" ")}
    >
      {creator.photoPath ? (
        <img
          alt={creator.name}
          className={[
            "h-10 w-10 rounded-full",
            "border border-[var(--color-border)]",
            "object-cover",
          ].join(" ")}
          src={creator.photoPath}
        />
      ) : (
        <span
          aria-hidden="true"
          className={[
            "flex h-10 w-10 items-center justify-center",
            "rounded-full",
            "bg-[var(--color-brand-surface)]",
            "font-semibold text-[var(--color-brand)]",
          ].join(" ")}
        >
          {creator.initials}
        </span>
      )}

      <span>
        {creator.label}{" "}
        <strong className="text-[var(--color-text)]">
          {creator.name}
        </strong>
      </span>

      {creator.linkedInUrl && (
        <a
          aria-label={creator.linkedInLabel}
          className={[
            "inline-flex min-h-11 items-center",
            "gap-[var(--space-1)]",
            "font-medium text-[var(--color-brand)]",
            "hover:underline",
          ].join(" ")}
          href={creator.linkedInUrl}
          rel="noreferrer"
          target="_blank"
        >
          <span
            aria-hidden="true"
            className={[
              "inline-flex h-5 w-5 items-center justify-center",
              "rounded-sm bg-[var(--color-brand)]",
              "text-xs font-bold text-white",
            ].join(" ")}
          >
            in
          </span>

          LinkedIn
        </a>
      )}
    </div>
  );
}
