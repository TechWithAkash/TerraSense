import { Activity, MapPinned } from "lucide-react";

const PROVENANCE_STYLES = {
  user: { label: "You told us", color: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" },
  inferred: { label: "Assumed", color: "border-amber-500/30 bg-amber-500/10 text-amber-300" },
  fetched: { label: "Looked up", color: "border-sky-500/30 bg-sky-500/10 text-sky-300" },
};

function humanizeKey(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function SitePanel({ siteState }) {
  const entries = Object.entries(siteState || {});

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-300">
        <Activity className="h-3.5 w-3.5 text-emerald-400" />
        Site state
      </div>

      {entries.length === 0 ? (
        <div className="mt-3 flex flex-col items-center gap-2 rounded-xl border border-dashed border-white/10 px-3 py-6 text-center">
          <MapPinned className="h-5 w-5 text-slate-600" />
          <p className="text-xs text-slate-500">Nothing known yet — start describing your land in the chat.</p>
        </div>
      ) : (
        <ul className="mt-3 divide-y divide-white/5">
          {entries.map(([key, value]) => {
            const isTracked = value && typeof value === "object" && "value" in value;
            const displayValue = isTracked ? value.value : value;
            const provenance = isTracked ? PROVENANCE_STYLES[value.provenance] : null;

            return (
              <li key={key} className="flex items-center justify-between gap-2 py-2 text-sm">
                <span className="text-slate-400">{humanizeKey(key)}</span>
                <span className="flex items-center gap-1.5">
                  <span className="font-mono text-xs text-slate-200">{String(displayValue)}</span>
                  {provenance && (
                    <span className={`rounded-full border px-1.5 py-0.5 text-[10px] font-semibold ${provenance.color}`}>
                      {provenance.label}
                    </span>
                  )}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
