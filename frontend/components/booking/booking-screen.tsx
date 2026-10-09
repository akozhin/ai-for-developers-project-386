"use client";

import { useCallback, useMemo, useState } from "react";

import "@/lib/api/client";
import {
  createBooking,
  getEventTypeSlots,
  getProfile,
  listEventTypes,
} from "@/lib/api/generated";
import type { Booking, EventType, Slot } from "@/lib/api/generated";
import {
  dateKey,
  groupSlotsByDate,
  longDateLabel,
  shiftMonth,
  timeLabel,
} from "@/lib/booking/time";
import { useResource } from "@/lib/booking/use-resource";

import { BookingForm, isFormValid } from "./booking-form";
import type { BookingFormValues, BookingSummary } from "./booking-form";
import { Calendar } from "./calendar";
import { Confirmation } from "./confirmation";
import { EventTypeSwitcher } from "./event-type-switcher";
import { ProfileHeader } from "./profile-header";
import type { TimeZoneOption } from "./profile-header";
import { SlotList } from "./slot-list";

const CONFLICT_MESSAGES: Record<string, string> = {
  slot_taken: "Слот только что заняли",
  slot_not_available: "Время недоступно, выберите другое",
};
const GENERIC_ERROR = "Не удалось забронировать, попробуйте ещё раз";

function errorCode(error: unknown): string | undefined {
  if (typeof error === "object" && error !== null && "code" in error) {
    const { code } = error;
    return typeof code === "string" ? code : undefined;
  }
  return undefined;
}

function browserTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

function Notice({
  children,
  onRetry,
}: {
  children: string;
  onRetry?: () => void;
}) {
  return (
    <div role="status" className="flex flex-col items-start gap-2 text-sm">
      <p className="text-muted-foreground">{children}</p>
      {onRetry ? (
        <button type="button" onClick={onRetry} className="underline">
          Повторить
        </button>
      ) : null}
    </div>
  );
}

export function BookingScreen({
  guestTimeZone = browserTimeZone(),
}: {
  guestTimeZone?: string;
}) {
  const [reloadKey, setReloadKey] = useState(0);
  const [slotsVersion, setSlotsVersion] = useState(0);

  const loadProfile = useCallback(
    async () => (await getProfile({ throwOnError: true })).data,
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reloadKey нужен для повтора
    [reloadKey],
  );
  const loadEventTypes = useCallback(
    async () => (await listEventTypes({ throwOnError: true })).data.items,
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reloadKey нужен для повтора
    [reloadKey],
  );
  const profile = useResource(loadProfile);
  const eventTypes = useResource(loadEventTypes);

  const [chosenTypeId, setChosenTypeId] = useState<string | null>(null);
  const types = eventTypes.status === "ready" ? eventTypes.data : [];
  const selectedType: EventType | undefined =
    types.find((type) => type.id === chosenTypeId) ?? types[0];

  const loadSlots = useCallback(async () => {
    if (!selectedType) return null;
    const { data } = await getEventTypeSlots({
      path: { id: selectedType.id },
      throwOnError: true,
    });
    return data;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- slotsVersion перезагружает слоты
  }, [selectedType?.id, slotsVersion]);
  const slots = useResource(loadSlots);

  const [zoneMode, setZoneMode] = useState<TimeZoneOption["value"]>("owner");
  const ownerZone = profile.status === "ready" ? profile.data.timezone : "UTC";
  const sameZone = guestTimeZone === ownerZone;
  const timeZone =
    zoneMode === "guest" && !sameZone ? guestTimeZone : ownerZone;

  const slotsByDate = useMemo(
    () =>
      slots.status === "ready" && slots.data
        ? groupSlotsByDate(slots.data.days, timeZone)
        : new Map<string, Slot[]>(),
    [slots, timeZone],
  );
  const enabledDates = useMemo(
    () => [...slotsByDate.keys()].sort(),
    [slotsByDate],
  );

  const [chosenDate, setChosenDate] = useState<string | null>(null);
  const selectedDate =
    chosenDate && enabledDates.includes(chosenDate)
      ? chosenDate
      : (enabledDates[0] ?? null);
  const [chosenMonth, setChosenMonth] = useState<string | null>(null);

  const windowMonths = useMemo(() => {
    const dates =
      slots.status === "ready" && slots.data
        ? [...slots.data.days.map((day) => day.date), ...enabledDates]
        : enabledDates;
    return [...new Set(dates.map((date) => date.slice(0, 7)))].sort();
  }, [slots, enabledDates]);
  const month =
    chosenMonth && windowMonths.includes(chosenMonth)
      ? chosenMonth
      : (selectedDate?.slice(0, 7) ?? windowMonths[0] ?? null);

  const [chosenSlot, setChosenSlot] = useState<string | null>(null);
  const daySlots = selectedDate ? (slotsByDate.get(selectedDate) ?? []) : [];
  const selectedSlot =
    daySlots.find((slot) => slot.starts_at === chosenSlot) ?? null;

  const [form, setForm] = useState<BookingFormValues>({
    name: "",
    email: "",
    comment: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [booked, setBooked] = useState<{
    booking: Booking;
    summary: BookingSummary;
  } | null>(null);

  function summaryFor(startsAt: string, endsAt: string, type: EventType) {
    return {
      dateLabel: longDateLabel(dateKey(startsAt, timeZone)),
      timeRange: `${timeLabel(startsAt, timeZone)}–${timeLabel(endsAt, timeZone)}`,
      durationMinutes: type.duration_minutes,
      timeZone,
    } satisfies BookingSummary;
  }

  const summary: BookingSummary | null =
    selectedSlot && selectedType
      ? summaryFor(selectedSlot.starts_at, selectedSlot.ends_at, selectedType)
      : null;

  async function submit() {
    if (!selectedSlot || !selectedType || !isFormValid(form)) return;
    setSubmitting(true);
    setBookingError(null);
    try {
      const result = await createBooking({
        body: {
          event_type_id: selectedType.id,
          starts_at: selectedSlot.starts_at,
          guest_name: form.name.trim(),
          guest_email: form.email.trim(),
          ...(form.comment.trim() ? { comment: form.comment.trim() } : {}),
        },
      });
      if (result.response?.ok && result.data) {
        setBooked({
          booking: result.data,
          summary: summaryFor(
            result.data.starts_at,
            result.data.ends_at,
            selectedType,
          ),
        });
      } else {
        setBookingError(
          CONFLICT_MESSAGES[errorCode(result.error) ?? ""] ?? GENERIC_ERROR,
        );
        setChosenSlot(null);
      }
    } catch {
      setBookingError(GENERIC_ERROR);
    } finally {
      setSubmitting(false);
      setSlotsVersion((version) => version + 1);
    }
  }

  function bookAnother() {
    setBooked(null);
    setChosenSlot(null);
    setBookingError(null);
    setForm((current) => ({ ...current, comment: "" }));
  }

  const zoneOptions: TimeZoneOption[] = sameZone
    ? [{ value: "owner", label: ownerZone }]
    : [
        { value: "owner", label: `${ownerZone} (владельца)` },
        { value: "guest", label: `${guestTimeZone} (ваш пояс)` },
      ];

  if (profile.status === "error" || eventTypes.status === "error") {
    return (
      <main className="mx-auto w-full max-w-5xl p-6">
        <Notice onRetry={() => setReloadKey((key) => key + 1)}>
          Не удалось загрузить данные. Проверьте соединение и повторите.
        </Notice>
      </main>
    );
  }
  if (profile.status === "loading" || eventTypes.status === "loading") {
    return (
      <main className="mx-auto w-full max-w-5xl p-6">
        <Notice>Загрузка…</Notice>
      </main>
    );
  }

  const canGoBack = month !== null && windowMonths.indexOf(month) > 0;
  const canGoForward =
    month !== null && windowMonths.indexOf(month) < windowMonths.length - 1;

  return (
    <main className="mx-auto grid w-full max-w-5xl gap-6 p-4 sm:p-6 lg:grid-cols-[1fr_22rem]">
      <section className="flex flex-col gap-6 rounded-2xl border bg-card p-4 text-card-foreground sm:p-6">
        <h1 className="text-lg font-semibold">Запланировать встречу</h1>
        <ProfileHeader
          profile={profile.data}
          timeZoneLabel={timeZone}
          options={zoneOptions}
          selected={sameZone ? "owner" : zoneMode}
          onSelect={setZoneMode}
        />
        {selectedType ? (
          <EventTypeSwitcher
            eventTypes={types}
            selectedId={selectedType.id}
            onSelect={(id) => {
              setChosenTypeId(id);
              setChosenSlot(null);
              setBookingError(null);
            }}
          />
        ) : (
          <Notice>Пока нет доступных типов событий.</Notice>
        )}

        {selectedType && slots.status === "loading" ? (
          <Notice>Загружаем свободное время…</Notice>
        ) : null}
        {selectedType && slots.status === "error" ? (
          <Notice onRetry={() => setSlotsVersion((version) => version + 1)}>
            Не удалось загрузить свободное время.
          </Notice>
        ) : null}
        {slots.status === "ready" && selectedType ? (
          enabledDates.length === 0 || month === null ? (
            <Notice>В ближайшие 14 дней свободного времени нет.</Notice>
          ) : (
            <div className="grid gap-6 md:grid-cols-[1fr_14rem]">
              <Calendar
                month={month}
                enabledDates={new Set(enabledDates)}
                selectedDate={selectedDate}
                canGoBack={canGoBack}
                canGoForward={canGoForward}
                onSelectDate={(date) => {
                  setChosenDate(date);
                  setChosenSlot(null);
                }}
                onShiftMonth={(delta) =>
                  setChosenMonth(shiftMonth(month, delta))
                }
              />
              {selectedDate ? (
                <SlotList
                  date={selectedDate}
                  slots={daySlots}
                  timeZone={timeZone}
                  selectedStart={selectedSlot?.starts_at ?? null}
                  onSelect={(startsAt) => {
                    setChosenSlot(startsAt);
                    setBookingError(null);
                  }}
                />
              ) : null}
            </div>
          )
        ) : null}
      </section>

      <aside className="h-fit rounded-2xl border bg-card p-4 text-card-foreground sm:p-6">
        {booked && selectedType ? (
          <Confirmation
            title={booked.booking.event_type.title}
            summary={booked.summary}
            email={booked.booking.guest_email}
            onBookAnother={bookAnother}
          />
        ) : (
          <BookingForm
            summary={summary}
            values={form}
            submitting={submitting}
            errorMessage={bookingError}
            onChange={setForm}
            onSubmit={submit}
          />
        )}
      </aside>
    </main>
  );
}
