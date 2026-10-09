import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function BookPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">Выбор времени</h1>
      <p className="max-w-md text-muted-foreground">
        Здесь появится выбор свободного слота. Раздел скоро заработает.
      </p>
      <Link href="/" className={buttonVariants({ variant: "outline" })}>
        Назад
      </Link>
    </main>
  );
}
