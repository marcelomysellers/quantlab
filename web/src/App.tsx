import { useEffect, useState } from "react";
import type { Manifest, Row } from "./types";
import { loadLeaderboard, loadManifest } from "./data";
import { useRoute, href } from "./router";
import { useTheme } from "./theme";
import { Ranking } from "./pages/Ranking";
import { Strategy } from "./pages/Strategy";
import { Duel } from "./pages/Duel";
import { Timeframes } from "./pages/Timeframes";
import { Method } from "./pages/Method";

export default function App() {
  const route = useRoute();
  const [theme, setTheme] = useTheme();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    Promise.all([loadLeaderboard(), loadManifest()]).then(([r, m]) => { setRows(r); setManifest(m); }).catch((e) => setErr(String(e)));
  }, []);

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
          {tab("metodo", "Método", href.metodo())}
        </nav>
        <span className="spacer" />
        <button className="ghost" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="alternar tema">{theme === "dark" ? "☀ claro" : "☾ escuro"}</button>
      </header>
      <main className="main">
        {err && <div className="card"><div className="empty">Não encontrei resultados em <code>results/latest/</code>. Rode <code>python -m quantlab.cli tournament --publish</code>.<br /><span className="muted">{err}</span></div></div>}
        {!err && (!rows || !manifest) && <div className="card"><div className="empty">carregando resultados…</div></div>}
        {rows && manifest && route.page === "ranking" && <Ranking rows={rows} manifest={manifest} />}
        {rows && manifest && route.page === "estrategia" && <Strategy id={route.id} manifest={manifest} themeKey={theme} />}
        {rows && manifest && route.page === "duelo" && <Duel rows={rows} a={route.a} b={route.b} themeKey={theme} />}
        {rows && manifest && route.page === "timeframes" && <Timeframes rows={rows} manifest={manifest} themeKey={theme} />}
        {rows && manifest && route.page === "metodo" && <Method manifest={manifest} />}
      </main>
    </div>
  );
}
