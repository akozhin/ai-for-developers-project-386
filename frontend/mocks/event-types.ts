import type { EventType } from "@/lib/api/generated";

export const mockEventTypes: EventType[] = [
  {
    id: "call-30",
    title: "Консультация",
    description: "Короткий созвон: знакомство или быстрый вопрос",
    duration_minutes: 30,
  },
  {
    id: "call-60",
    title: "Разбор кода",
    description: "Подробный разбор задачи или проекта",
    duration_minutes: 60,
  },
];
