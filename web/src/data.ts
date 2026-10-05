import type { Detail, Duel, Manifest, Row } from "./types";

const base = `${import.meta.env.BASE_URL}results/latest/`;
const cache = new Map<string, Promise<unknown>>();

function getJson<T>(path: string): Promise<T> {
  if (!cache.has(path)) {
    cache.set(path, fetch(base + path).then((r) => {
      if (!r.ok) throw new Error(`falha ao carregar ${path}: ${r.status}`);
      return r.json();
    }));
  }
  return cache.get(path) as Promise<T>;
}

export const loadLeaderboard = () => getJson<Row[]>("leaderboard.json");
export const loadManifest = () => getJson<Manifest>("manifest.json");
export const loadDuels = () => getJson<Duel[]>("duels.json");
export const loadEntry = (id: string) => getJson<Detail>(`entries/${id}.json`);
