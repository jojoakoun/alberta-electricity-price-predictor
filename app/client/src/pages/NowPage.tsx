import { Card } from "../components/Card";
import { StatusBadge } from "../components/StatusBadge";
import { copy } from "../copy";

export function NowPage() {
  return (
    <div className="space-y-[var(--space-4)]">
      <header className="space-y-[var(--space-2)]">
        <h1>{copy.pages.now.title}</h1>
      </header>

      <Card className="space-y-[var(--space-3)]">
        <StatusBadge level="unavailable" />

        <p className="text-[var(--color-text-muted)]">
          {copy.recommendations.unavailable.defaultExplanation}
        </p>
      </Card>
    </div>
  );
}
