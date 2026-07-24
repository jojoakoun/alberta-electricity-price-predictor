import {
  ArrowUpRight,
  MapPin,
} from "lucide-react";
import { useState } from "react";

import { Card } from "../Card";
import { Reveal } from "../motion/Reveal";
import { copy } from "../../copy";

export function DeveloperProfile() {
  const developer = copy.projectPage.developer;
  const [photoUnavailable, setPhotoUnavailable] = useState(false);

  return (
    <Reveal>
      <section aria-labelledby="meet-developer">
        <Card
          className={[
            "project-developer-card",
            "grid gap-[var(--space-6)]",
            "sm:grid-cols-[13rem_minmax(0,1fr)]",
            "sm:items-center",
            "sm:p-[var(--space-6)]",
          ].join(" ")}
        >
          <div className="project-developer-photo-wrap">
            {photoUnavailable ? (
              <div
                aria-label={developer.photoFallbackLabel}
                className="project-developer-avatar-fallback"
                role="img"
              >
                {developer.initials}
              </div>
            ) : (
              <img
                alt={developer.name}
                className={[
                  "aspect-square w-40",
                  "rounded-full object-cover",
                  "sm:w-48",
                ].join(" ")}
                onError={() => setPhotoUnavailable(true)}
                src={developer.photoPath}
              />
            )}
          </div>

          <div className="project-developer-copy space-y-[var(--space-4)]">
            <div className="space-y-[var(--space-2)]">
              <p
                className={[
                  "project-developer-eyebrow",
                  "font-semibold uppercase tracking-wide",
                  "text-[var(--font-size-caption)]",
                  "text-[var(--color-brand)]",
                ].join(" ")}
              >
                {developer.title}
              </p>

              <h2
                id="meet-developer"
                className="project-developer-name"
              >
                {developer.name}
              </h2>

              <p className="project-developer-roles font-semibold">
                {developer.roles}
              </p>
            </div>

            <p
              className={[
                "inline-flex items-center",
                "gap-[var(--space-2)]",
                "text-[var(--color-text-muted)]",
              ].join(" ")}
            >
              <MapPin aria-hidden="true" size={18} />
              {developer.location}
            </p>

            <p
              className={[
                "max-w-2xl",
                "leading-relaxed",
                "text-[var(--color-text-muted)]",
              ].join(" ")}
            >
              {developer.description}
            </p>

            <p
              className={[
                "text-[var(--font-size-caption)]",
                "text-[var(--color-text-muted)]",
              ].join(" ")}
            >
              {developer.education}
            </p>

            <a
              className="project-link-button"
              href={developer.linkedInUrl}
              rel="noreferrer"
              target="_blank"
            >
              {developer.linkedInLabel}

              <ArrowUpRight
                aria-hidden="true"
                size={18}
              />
            </a>
          </div>
        </Card>
      </section>
    </Reveal>
  );
}
