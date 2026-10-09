import { CalendarDays, Clock, Globe, Video } from "lucide-react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export type BookingFormValues = {
  name: string;
  email: string;
  comment: string;
};

export type BookingSummary = {
  dateLabel: string;
  timeRange: string;
  durationMinutes: number;
  timeZone: string;
};

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const MAX_NAME = 100;
const MAX_COMMENT = 500;

export function isEmailValid(email: string): boolean {
  return EMAIL_PATTERN.test(email.trim());
}

export function isFormValid(values: BookingFormValues): boolean {
  return (
    values.name.trim().length > 0 &&
    values.name.length <= MAX_NAME &&
    isEmailValid(values.email) &&
    values.comment.length <= MAX_COMMENT
  );
}

export function BookingForm({
  summary,
  values,
  submitting,
  errorMessage,
  onChange,
  onSubmit,
}: {
  summary: BookingSummary | null;
  values: BookingFormValues;
  submitting: boolean;
  errorMessage: string | null;
  onChange: (values: BookingFormValues) => void;
  onSubmit: () => void;
}) {
  const emailInvalid = values.email.length > 0 && !isEmailValid(values.email);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (summary && isFormValid(values) && !submitting) onSubmit();
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-2xl font-semibold tracking-tight">
        Подтвердить встречу
      </h2>
      {summary ? (
        <ul
          aria-label="Выбранная встреча"
          className="flex flex-col gap-2 rounded-lg border bg-background p-3 text-sm"
        >
          <li className="flex items-center gap-2">
            <CalendarDays className="size-4 text-muted-foreground" />
            {summary.dateLabel} · {summary.timeRange}
          </li>
          <li className="flex items-center gap-2">
            <Clock className="size-4 text-muted-foreground" />
            {summary.durationMinutes} мин
          </li>
          <li className="flex items-center gap-2">
            <Video className="size-4 text-muted-foreground" />
            Видеозвонок
          </li>
          <li className="flex items-center gap-2">
            <Globe className="size-4 text-muted-foreground" />
            {summary.timeZone}
          </li>
        </ul>
      ) : (
        <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
          Выберите дату и время, чтобы продолжить.
        </p>
      )}

      <label className="flex flex-col gap-1.5 text-sm font-medium">
        <span>
          Ваше имя <span className="text-destructive">*</span>
        </span>
        <Input
          value={values.name}
          maxLength={MAX_NAME}
          autoComplete="name"
          onChange={(event) =>
            onChange({ ...values, name: event.target.value })
          }
        />
      </label>
      <label className="flex flex-col gap-1.5 text-sm font-medium">
        <span>
          Электронная почта <span className="text-destructive">*</span>
        </span>
        <Input
          type="email"
          value={values.email}
          autoComplete="email"
          aria-invalid={emailInvalid}
          aria-describedby={emailInvalid ? "email-error" : undefined}
          onChange={(event) =>
            onChange({ ...values, email: event.target.value })
          }
        />
      </label>
      {emailInvalid ? (
        <span
          id="email-error"
          role="alert"
          className="-mt-2 text-xs text-destructive"
        >
          Укажите корректный адрес электронной почты
        </span>
      ) : null}
      <label className="flex flex-col gap-1.5 text-sm font-medium">
        <span>
          Комментарий{" "}
          <span className="font-normal text-muted-foreground">
            (необязательно)
          </span>
        </span>
        <Textarea
          value={values.comment}
          maxLength={MAX_COMMENT}
          placeholder="Например, тема встречи или вопросы для обсуждения"
          onChange={(event) =>
            onChange({ ...values, comment: event.target.value })
          }
        />
      </label>

      {errorMessage ? (
        <p role="alert" className="text-sm text-destructive">
          {errorMessage}
        </p>
      ) : null}
      <Button
        type="submit"
        size="lg"
        disabled={!summary || !isFormValid(values) || submitting}
      >
        {submitting ? "Бронируем…" : "Забронировать"}
      </Button>
    </form>
  );
}
