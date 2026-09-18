"use client";

import { useState } from "react";
import { AlertTriangle, BookOpen, ChevronDown, Clock, Coins, TrendingUp } from "lucide-react";

const CONFIDENCE_STYLES = {
  High: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  "Medium-High": "border-teal-500/30 bg-teal-500/10 text-teal-300",
  Medium: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  Low: "border-rose-500/30 bg-rose-500/10 text-rose-300",
};

const HORIZON_LABELS = {
  short_term: "Short term",
  medium_term: "Medium term",
  long_term: "Long term",
};

function formatRange(low, high, unit) {
  const sign = (value) => (value > 0 ? "+" : "");
  return `${sign(low)}${low} → ${sign(high)}${high} ${unit}`.trim();
}

export default function RecommendationCard({ recommendation }) {
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const confidenceStyle = CONFIDENCE_STYLES[recommendation.confidence.band] || CONFIDENCE_STYLES.Medium;

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-emerald-400">
            #{recommendation.rank} recommendation
          </span>
          <h3 className="mt-1 text-lg font-semibold text-white">{recommendation.what_to_do}</h3>
        </div>
        <span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold ${confidenceStyle}`}>
          {recommendation.confidence.band} · {Math.round(recommendation.confidence.score * 100)}%
        </span>
      </div>

      <div className="mt-3 flex items-start gap-2 rounded-xl border border-white/5 bg-black/20 p-3">
        <TrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
        <p className="text-sm leading-relaxed text-slate-300">{recommendation.why_it_works}</p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Impacted metrics</h4>
          <ul className="mt-2 space-y-1.5">
            {recommendation.impacted_metrics.map((metric) => (
              <li key={metric.variable} className="flex items-center justify-between gap-2 text-sm">
                <span className="text-slate-300">{metric.label}</span>
                <span className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-xs text-emerald-300">
                  {formatRange(metric.projected_low, metric.projected_high, metric.unit)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-2.5 text-sm">
          <div className="flex items-center gap-2 text-slate-300">
            <Clock className="h-3.5 w-3.5 text-slate-500" />
            {HORIZON_LABELS[recommendation.time_horizon] || recommendation.time_horizon}
          </div>
          {recommendation.cost_inr_per_ha && (
            <div className="flex items-center gap-2 text-slate-300">
              <Coins className="h-3.5 w-3.5 text-slate-500" />₹{recommendation.cost_inr_per_ha[0].toLocaleString("en-IN")}
              {" – "}₹{recommendation.cost_inr_per_ha[1].toLocaleString("en-IN")} / ha
            </div>
          )}
        </div>
      </div>

      {recommendation.trade_offs.length > 0 && (
        <div className="mt-4 rounded-xl border border-amber-500/25 bg-amber-500/[0.07] p-3.5">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-amber-300">
            <AlertTriangle className="h-3.5 w-3.5" />
            Trade-off to weigh
          </div>
          {recommendation.trade_offs.map((tradeOff) => (
            <div key={tradeOff.variable} className="mt-1.5 text-sm text-amber-100/90">
              <p>
                {tradeOff.label} {tradeOff.direction} by {tradeOff.magnitude}.
              </p>
              {tradeOff.mitigation && (
                <p className="mt-1 border-l-2 border-amber-500/30 pl-2 text-xs italic text-amber-200/70">
                  Mitigation: {tradeOff.mitigation}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 border-t border-white/10 pt-3">
        <button
          onClick={() => setEvidenceOpen((prev) => !prev)}
          className="flex w-full items-center justify-between text-left text-xs font-semibold uppercase tracking-wide text-slate-400 transition hover:text-emerald-300"
        >
          <span className="flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5" />
            Evidence ({recommendation.evidence.length} sources)
          </span>
          <ChevronDown className={`h-4 w-4 transition-transform ${evidenceOpen ? "rotate-180" : ""}`} />
        </button>

        {evidenceOpen && (
          <ul className="mt-3 space-y-2.5">
            {recommendation.evidence.map((claim) => (
              <li key={claim.claim_id} className="rounded-lg border border-white/5 bg-black/20 p-2.5 text-xs">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="font-medium text-slate-200">
                    {claim.document} ({claim.year})
                  </span>
                  <span className="rounded bg-white/5 px-1.5 py-0.5 uppercase text-slate-400">{claim.study_design}</span>
                </div>
                <p className="mt-1 text-slate-400">{claim.summary}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
