import type { Detail, Duel, Manifest, Row } from "./types";

export interface RunInfo { id: string; symbol: string; instrument: string; start: string; end: string; tfs: string[]; generated_at: string }

const root = `${import.meta.env.BASE_URL}results/`;
const cache = new Map<string, Promise<unknown>>();
let activeRun = "";

function getJson<T>(path: string): Promise<T> {
  if (!cache.has(path)) {
    cache.set(path, fetch(root + path).then((r) => {
      if (!r.ok) throw new Error(`falha ao carregar ${path}: ${r.status}`);
      return r.json();
    }));
  }
  return cache.get(path) as Promise<T>;
}

export const loadIndex = () => getJson<RunInfo[]>("index.json");
export const setActiveRun = (id: string) => { activeRun = id; };
export const getActiveRun = () => activeRun;
const base = () => `${activeRun}/`;

export const loadLeaderboard = () => getJson<Row[]>(base() + "leaderboard.json");
export const loadManifest = () => getJson<Manifest>(base() + "manifest.json");
export const loadDuels = () => getJson<Duel[]>(base() + "duels.json");
export const loadEntry = (id: string) => getJson<Detail>(`${base()}entries/${id}.json`);
