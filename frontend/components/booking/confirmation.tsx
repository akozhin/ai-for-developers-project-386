import { CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { BookingSummary } from "./booking-form";

export function Confirmation({
  title,
  summary,
  email,
  onBookAnother,
}: {
  title: string;
  summary: BookingSummary;
  email: string;
  onBookAnother: () => void;
}) {
  return (
    <div role="status" className="flex flex-col gap-4">
      <CheckCircle2 aria-hidden className="size-10 text-primary" />
      <h2 className="text-2xl font-semibold tracking-tight">
        Встреча забронирована
      </h2>
      <p className="text-sm">
        {title}: {summary.dateLabel} · {summary.timeRange} (
        {summary.durationMinutes} мин, {summary.timeZone}).
      </p>
      <p className="text-sm text-muted-foreground">
        Мы запомнили ваш адрес {email}.
      </p>
      <Button variant="outline" size="lg" onClick={onBookAnother}>
        Забронировать ещё
      </Button>
    </div>
  );
}
