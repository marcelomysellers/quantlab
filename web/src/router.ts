import { useEffect, useState } from "react";

export type Route =
  | { page: "ranking" }
  | { page: "estrategia"; id: string }
  | { page: "duelo"; a?: string; b?: string }
  | { page: "timeframes" }
  | { page: "metodo" };

export function parseHash(): Route {
  const h = location.hash.replace(/^#\/?/, "");
  const [path, query] = h.split("?");
  const parts = path.split("/");
  const q = new URLSearchParams(query || "");
  switch (parts[0]) {
    case "estrategia": return { page: "estrategia", id: decodeURIComponent(parts[1] || "") };
    case "duelo": return { page: "duelo", a: q.get("a") || undefined, b: q.get("b") || undefined };
    case "timeframes": return { page: "timeframes" };
    case "metodo": return { page: "metodo" };
    default: return { page: "ranking" };
  }
}

export function useRoute(): Route {
  const [route, setRoute] = useState<Route>(parseHash);
  useEffect(() => {
    const on = () => setRoute(parseHash());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}

export const href = {
  ranking: () => "#/ranking",
  estrategia: (id: string) => `#/estrategia/${encodeURIComponent(id)}`,
  duelo: (a?: string, b?: string) => `#/duelo${a || b ? `?${new URLSearchParams({ ...(a ? { a } : {}), ...(b ? { b } : {}) }).toString()}` : ""}`,
  timeframes: () => "#/timeframes",
  metodo: () => "#/metodo",
};
