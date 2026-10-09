import { useEffect, useRef, useState } from "react";

export type Resource<T> =
  { status: "loading" } | { status: "error" } | { status: "ready"; data: T };

type Loaded<T> = { key: string; version: number; value: Resource<T> };

/**
 * Загружает данные при смене `key` (другой ресурс) или `version` (повторная загрузка того же).
 * Устаревшие ответы отбрасываются. При смене только `version` пока идёт загрузка остаются
 * прежние данные, чтобы интерфейс не мерцал; при смене `key` показывается `loading`.
 */
export function useResource<T>(
  load: () => Promise<T>,
  key: string,
  version = 0,
): Resource<T> {
  const [state, setState] = useState<Loaded<T> | null>(null);
  const latestLoad = useRef(load);

  useEffect(() => {
    latestLoad.current = load;
  });

  useEffect(() => {
    let active = true;
    latestLoad
      .current()
      .then((data) => {
        if (active)
          setState({ key, version, value: { status: "ready", data } });
      })
      .catch(() => {
        if (active) setState({ key, version, value: { status: "error" } });
      });
    return () => {
      active = false;
    };
  }, [key, version]);

  if (state?.key === key && state.version === version) return state.value;
  if (state?.key === key && state.value.status === "ready") return state.value;
  return { status: "loading" };
}
