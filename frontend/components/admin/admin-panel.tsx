"use client";

import { useState } from "react";

import { BookingsTab } from "@/components/admin/bookings-tab";
import { EventTypesTab } from "@/components/admin/event-types-tab";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "bookings", label: "Встречи" },
  { id: "event-types", label: "Типы событий" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function AdminPanel() {
  const [active, setActive] = useState<TabId>("bookings");

  return (
    <div className="flex flex-col gap-6">
      <div role="tablist" className="flex gap-1 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            role="tab"
            type="button"
            aria-selected={active === tab.id}
            aria-controls={`panel-${tab.id}`}
            onClick={() => setActive(tab.id)}
            className={cn(
              "-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              active === tab.id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div
        role="tabpanel"
        id={`panel-${active}`}
        aria-labelledby={`tab-${active}`}
      >
        {active === "bookings" ? <BookingsTab /> : <EventTypesTab />}
      </div>
    </div>
  );
}
