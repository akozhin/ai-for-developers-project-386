import Image from "next/image";

import type { Profile } from "@/lib/api/generated";

export type TimeZoneOption = { value: "owner" | "guest"; label: string };

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
}

export function ProfileHeader({
  profile,
  timeZoneLabel,
  options,
  selected,
  onSelect,
}: {
  profile: Profile;
  timeZoneLabel: string;
  options: TimeZoneOption[];
  selected: TimeZoneOption["value"];
  onSelect: (value: TimeZoneOption["value"]) => void;
}) {
  return (
    <header className="flex flex-wrap items-center gap-4">
      {profile.avatar_url ? (
        <Image
          src={profile.avatar_url}
          alt={profile.name}
          width={56}
          height={56}
          unoptimized
          className="size-14 rounded-full object-cover"
        />
      ) : (
        <div
          aria-hidden
          className="flex size-14 items-center justify-center rounded-full border bg-muted text-lg font-semibold"
        >
          {initials(profile.name)}
        </div>
      )}
      <div className="min-w-40 flex-1">
        <p className="text-xl font-semibold">{profile.name}</p>
        <p className="text-sm text-muted-foreground">
          Видеозвонок · {timeZoneLabel}
        </p>
      </div>
      <label className="flex w-full items-center gap-2 text-sm text-muted-foreground sm:w-auto">
        <span className="sr-only sm:not-sr-only">Часовой пояс</span>
        <select
          aria-label="Часовой пояс"
          value={selected}
          onChange={(event) =>
            onSelect(event.target.value === "guest" ? "guest" : "owner")
          }
          className="h-9 min-w-0 flex-1 rounded-lg border border-input bg-background px-2 text-sm text-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 sm:flex-none"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </header>
  );
}
