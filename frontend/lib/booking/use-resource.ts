import { useEffect, useState } from "react";

export type Resource<T> =
  { status: "loading" } | { status: "error" } | { status: "ready"; data: T };

/**
 * Загружает данные при смене `load` (меняйте его через useCallback, чтобы перезагрузить).
 * Пока идёт новая загрузка, возвращает `loading`; устаревшие ответы отбрасываются.
 */
export function useResource<T>(load: () => Promise<T>): Resource<T> {
  const [state, setState] = useState<{
    source: () => Promise<T>;
    value: Resource<T>;
  } | null>(null);

  useEffect(() => {
    let active = true;
    load()
      .then((data) => {
        if (active)
          setState({ source: load, value: { status: "ready", data } });
      })
      .catch(() => {
        if (active) setState({ source: load, value: { status: "error" } });
      });
    return () => {
      active = false;
    };
  }, [load]);

  return state?.source === load ? state.value : { status: "loading" };
}
