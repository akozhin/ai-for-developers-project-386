import type { Metadata } from "next";

import { AdminPanel } from "@/components/admin/admin-panel";

export const metadata: Metadata = {
  title: "Владелец — Запись на звонок",
  robots: { index: false },
};

export default function AdminPage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">
        Кабинет владельца
      </h1>
      <AdminPanel />
    </main>
  );
}
