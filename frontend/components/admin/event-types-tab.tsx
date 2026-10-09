"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { browserApi } from "@/lib/api/browser";
import { createEventType, listEventTypes } from "@/lib/api/generated";
import type { EventType, FieldError } from "@/lib/api/generated";

type List =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; items: EventType[] };

type FormErrors = { general?: string; fields: Record<string, string> };

const EMPTY_FORM = { id: "", title: "", description: "", duration: "30" };

const inputClass =
  "h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-destructive";

export function EventTypesTab() {
  const [list, setList] = useState<List>({ status: "loading" });
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState<FormErrors>({ fields: {} });
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await listEventTypes({
        ...browserApi(),
        throwOnError: true,
      });
      setList({ status: "ready", items: data.items });
    } catch {
      setList({ status: "error" });
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- загрузка данных при открытии вкладки
    void load();
  }, [load]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setErrors({ fields: {} });
    try {
      const result = await createEventType({
        ...browserApi(),
        body: {
          id: form.id,
          title: form.title,
          description: form.description,
          duration_minutes: Number(form.duration),
        },
      });
      if (result.error === undefined) {
        setForm(EMPTY_FORM);
        await load();
      } else {
        setErrors(toFormErrors(result.error));
      }
    } catch {
      setErrors({ fields: {}, general: "Не удалось создать тип события" });
    } finally {
      setSubmitting(false);
    }
  }

  const field = (name: keyof typeof EMPTY_FORM, apiName: string = name) => ({
    value: form[name],
    "aria-invalid": errors.fields[apiName] ? true : undefined,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm({ ...form, [name]: e.target.value }),
  });

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-4">
        <h2 className="text-2xl font-semibold tracking-tight">Типы событий</h2>
        {list.status === "loading" ? (
          <p className="text-muted-foreground">Загрузка…</p>
        ) : list.status === "error" ? (
          <p role="alert" className="text-destructive">
            Не удалось загрузить типы событий
          </p>
        ) : list.items.length === 0 ? (
          <p className="text-muted-foreground">Типов событий пока нет</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {list.items.map((item) => (
              <li
                key={item.id}
                className="flex flex-col gap-1 rounded-xl border border-border bg-card p-4 text-card-foreground"
              >
                <span className="font-medium">{item.title}</span>
                <span className="text-sm text-muted-foreground">
                  {item.id} · {item.duration_minutes} минут
                </span>
                <span className="text-sm">{item.description}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        <h2 className="text-2xl font-semibold tracking-tight">Новый тип</h2>
        <Labeled label="Идентификатор" error={errors.fields.id}>
          <input className={inputClass} {...field("id")} />
        </Labeled>
        <Labeled label="Название" error={errors.fields.title}>
          <input className={inputClass} {...field("title")} />
        </Labeled>
        <Labeled label="Описание" error={errors.fields.description}>
          <input className={inputClass} {...field("description")} />
        </Labeled>
        <Labeled
          label="Длительность, минут"
          error={errors.fields.duration_minutes}
        >
          <input
            className={inputClass}
            type="number"
            min={1}
            {...field("duration", "duration_minutes")}
          />
        </Labeled>
        {errors.general ? (
          <p role="alert" className="text-sm text-destructive">
            {errors.general}
          </p>
        ) : null}
        <Button type="submit" disabled={submitting} className="self-start">
          Создать
        </Button>
      </form>
    </div>
  );
}

function Labeled({
  label,
  error,
  children,
}: {
  label: string;
  error: string | undefined;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm font-medium">
      {label}
      {children}
      {error ? (
        <span className="font-normal text-destructive">{error}</span>
      ) : null}
    </label>
  );
}

function toFormErrors(error: unknown): FormErrors {
  const body = error as
    { code?: string; message?: string; fields?: FieldError[] } | undefined;
  if (body?.code === "validation_error" && body.fields) {
    return {
      fields: Object.fromEntries(
        body.fields.map(({ field, message }) => [field, message]),
      ),
    };
  }
  return {
    fields: {},
    general: body?.message ?? "Не удалось создать тип события",
  };
}
