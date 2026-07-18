import { Card } from "../components/Card";
import { copy } from "../copy";

export function LearnPage() {
  return (
    <div className="space-y-[var(--space-4)]">
      <header className="space-y-[var(--space-2)]">
        <h1>{copy.pages.learn.title}</h1>

        <p className="text-[var(--color-text-muted)]">
          {copy.pages.learn.description}
        </p>
      </header>

      <Card>
        <h2>How it works</h2>
      </Card>
    </div>
  );
}
