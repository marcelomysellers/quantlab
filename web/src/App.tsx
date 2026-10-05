import { useEffect, useState } from "react";
import type { Manifest, Row } from "./types";
import { loadIndex, loadLeaderboard, loadManifest, setActiveRun, type RunInfo } from "./data";
import { useRoute, href } from "./router";
import { useTheme } from "./theme";
import { Ranking } from "./pages/Ranking";
import { Strategy } from "./pages/Strategy";
import { Duel } from "./pages/Duel";
import { Timeframes } from "./pages/Timeframes";
import { Method } from "./pages/Method";
import { Signals } from "./pages/Signals";

export default function App() {
  const route = useRoute();
  const [theme, setTheme] = useTheme();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [runId, setRunId] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    loadIndex().then((list) => {
      setRuns(list);
      let wanted = "";
      try { wanted = localStorage.getItem("quantlab-run") || ""; } catch { /* sem storage */ }
      const first = list.find((r) => r.id === wanted) ?? list[0];
      if (first) setRunId(first.id);
    }).catch((e) => setErr(String(e)));
  }, []);
  useEffect(() => {
    if (!runId) return;
    setActiveRun(runId);
    setRows(null); setManifest(null);
    try { localStorage.setItem("quantlab-run", runId); } catch { /* ignora */ }
    Promise.all([loadLeaderboard(), loadManifest()]).then(([r, m]) => { setRows(r); setManifest(m); }).catch((e) => setErr(String(e)));
  }, [runId]);

  const tab = (page: string, label: string, link: string) => (
    <a key={page} className={`tab ${route.page === page ? "active" : ""}`} href={link}>{label}</a>
  );

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">Quant Lab<small>{manifest ? `${manifest.instrument} · ${manifest.start.slice(0, 4)}–${manifest.end.slice(0, 4)}` : ""}</small></span>
        <nav className="tabs">
          {tab("ranking", "Ranking", href.ranking())}
          {tab("timeframes", "Timeframes", href.timeframes())}
          {tab("duelo", "Duelo", href.duelo())}
          {tab("sinais", "Sinais", href.sinais())}
          {tab("metodo", "Método", href.metodo())}
        </nav>
        <span className="spacer" />
        {runs.length > 0 && (
          <select className="inline-select" value={runId} onChange={(e) => { setRunId(e.target.value); location.hash = href.ranking(); }} aria-label="torneio">
            {runs.map((r) => <option key={r.id} value={r.id}>{r.instrument} · {r.start.slice(0, 4)}–{r.end.slice(0, 4)} · {r.tfs.join(" ")}{r.wf_mode === "mean" ? " · média da grade" : ""} · método v{r.method_version ?? 1}</option>)}
          </select>
        )}
        <button className="ghost" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="alternar tema">{theme === "dark" ? "☀ claro" : "☾ escuro"}</button>
      </header>
      <main className="main">
        {err && <div className="card"><div className="empty">Não encontrei resultados em <code>web/public/results/</code>. Rode <code>python -m quantlab.cli tournament --publish</code>.<br /><span className="muted">{err}</span></div></div>}
        {!err && (!rows || !manifest) && <div className="card"><div className="empty">carregando resultados…</div></div>}
        {rows && manifest && route.page === "ranking" && <Ranking key={runId} rows={rows} manifest={manifest} />}
        {rows && manifest && route.page === "estrategia" && <Strategy key={runId + route.id} id={route.id} manifest={manifest} themeKey={theme} />}
        {rows && manifest && route.page === "duelo" && <Duel key={runId} rows={rows} a={route.a} b={route.b} themeKey={theme} />}
        {rows && manifest && route.page === "timeframes" && <Timeframes rows={rows} manifest={manifest} themeKey={theme} />}
        {rows && manifest && route.page === "metodo" && <Method manifest={manifest} />}
        {route.page === "sinais" && <Signals themeKey={theme} />}
      </main>
    </div>
  );
}
