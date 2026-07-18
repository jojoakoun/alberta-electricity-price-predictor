import { Card } from "../components/Card";
import { copy } from "../copy";

export function TodayPage() {
  return (
    <div className="space-y-[var(--space-4)]">
      <header className="space-y-[var(--space-2)]">
        <h1>{copy.pages.today.title}</h1>

        <p className="text-[var(--color-text-muted)]">
          {copy.pages.today.description}
        </p>
      </header>

      <Card>
        <p className="text-[var(--color-text-muted)]">
          Forecast cards will appear here.
        </p>
      </Card>
    </div>
  );
}
