import Link from "next/link";
import { Suspense } from "react";

import { EventTypesLoader } from "@/components/event-types-loader";
import { buttonVariants } from "@/components/ui/button";

const steps = [
  "Выберите тип звонка",
  "Выберите дату и свободное время",
  "Укажите имя и email — запись готова",
];

const benefits = [
  "Без регистрации: достаточно имени и email",
  "Занятое время сразу исчезает: двойная запись исключена",
];

export default function Home() {
  return (
    <>
      <main className="flex flex-1 flex-col items-center gap-16 px-6 py-16">
        <section className="flex flex-col items-center gap-6 text-center">
          <h1 className="text-4xl font-semibold tracking-tight">
            Запись на звонок
          </h1>
          <p className="max-w-md text-muted-foreground">
            Свободное время видно сразу, занять слот можно за один шаг.
          </p>
          <Link href="/book" className={buttonVariants({ size: "lg" })}>
            Записаться
          </Link>
        </section>

        <section className="flex w-full max-w-3xl flex-col gap-4">
          <h2 className="text-2xl font-semibold tracking-tight">
            Как это работает
          </h2>
          <ol
            aria-label="Как это работает"
            className="grid gap-4 sm:grid-cols-3"
          >
            {steps.map((step, index) => (
              <li
                key={step}
                className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 text-card-foreground"
              >
                <span className="text-sm text-muted-foreground">
                  Шаг {index + 1}
                </span>
                <span className="font-medium">{step}</span>
              </li>
            ))}
          </ol>
        </section>

        <Suspense fallback={null}>
          <EventTypesLoader />
        </Suspense>

        <section className="flex w-full max-w-3xl flex-col gap-4">
          <h2 className="text-2xl font-semibold tracking-tight">
            Почему удобно
          </h2>
          <ul className="flex flex-col gap-2 text-muted-foreground">
            {benefits.map((benefit) => (
              <li key={benefit}>{benefit}</li>
            ))}
          </ul>
        </section>
      </main>
      <footer className="px-6 py-6 text-center text-sm text-muted-foreground">
        Учебный проект Hexlet «AI for Developers»
      </footer>
    </>
  );
}
