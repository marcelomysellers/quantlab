import type { Verdict } from "./types";
import { VERDICT_LABEL } from "./format";

export function Badge({ v }: { v: Verdict }) {
  const icon = v === "aprovada" ? "✓" : v === "promissora" ? "◐" : v === "reprovada" ? "✕" : "·";
  return <span className={`badge ${v}`}><i aria-hidden="true" />{icon} {VERDICT_LABEL[v]}</span>;
}

export function Tile({ label, value, delta, cls }: { label: string; value: string; delta?: string; cls?: string }) {
  return (
    <div className="tile">
      <div className="label">{label}</div>
      <div className={`value ${cls ?? ""}`}>{value}</div>
      {delta && <div className="delta">{delta}</div>}
    </div>
  );
}
