"use client";

import { useState } from "react";

const HORIZON_LABELS = {
  short_term: "Short term (1–12 mos)",
  medium_term: "Medium term (1–3 yrs)",
  long_term: "Long term (3+ yrs)",
};

const CONFIDENCE_STYLES = {
  High: "bg-[#E8F7ED] text-[rgb(0,146,69)] border-[rgba(0,146,69,0.3)]",
  "Medium-High": "bg-[#E8F7ED] text-[rgb(0,146,69)] border-[rgba(0,146,69,0.3)]",
  Medium: "bg-[#FEF3C7] text-[#92400E] border-amber-200",
  Low: "bg-[#FEE2E2] text-[#991B1B] border-red-200",
};

function formatRange(low, high, unit) {
  const sign = (value) => (value > 0 ? "+" : "");
  return `${sign(low)}${low} → ${sign(high)}${high} ${unit}`.trim();
}

export default function RecommendationCard({ recommendation }) {
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const confStyle =
    CONFIDENCE_STYLES[recommendation.confidence.band] ||
    "bg-gray-100 text-gray-700 border-gray-200";

  return (
    <div
      className="group rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-[rgb(0,146,69)] hover:shadow-md"
      style={{ transitionDuration: "300ms", transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)" }}
    >
      {/* Top row: Rank & Title + Confidence pill */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-[#0B1F16] text-xs font-semibold text-[rgb(0,146,69)]">
            {recommendation.rank}
          </span>
          <div>
            <h4 className="text-base font-semibold text-gray-900 leading-snug">
              {recommendation.what_to_do}
            </h4>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
              <span className="font-medium text-gray-700">
                {HORIZON_LABELS[recommendation.time_horizon] || recommendation.time_horizon}
              </span>
              {recommendation.cost_inr_per_ha && (
                <>
                  <span>•</span>
                  <span>
                    ₹{recommendation.cost_inr_per_ha[0].toLocaleString("en-IN")} – ₹
                    {recommendation.cost_inr_per_ha[1].toLocaleString("en-IN")} / ha
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold ${confStyle}`}
        >
          {recommendation.confidence.band} · {Math.round(recommendation.confidence.score * 100)}%
        </span>
      </div>

      {/* Scientific explanation */}
      <p className="mt-3 text-sm leading-relaxed text-gray-700">
        {recommendation.why_it_works}
      </p>

      {/* Impacted Metrics Chips */}
      <div className="mt-4 rounded-xl bg-[#F3F4F6] p-3 border border-gray-100">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
          Impacted Environmental Metrics (Causal Propagation)
        </span>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {recommendation.impacted_metrics.map((metric) => (
            <div
              key={metric.variable}
              className="flex items-center justify-between rounded-lg bg-white px-3 py-1.5 border border-gray-200/80 shadow-2xs"
            >
              <span className="text-xs text-gray-700 font-medium truncate pr-2">
                {metric.label}
              </span>
              <span className="font-mono text-xs font-semibold text-[rgb(0,146,69)] shrink-0">
                {formatRange(metric.projected_low, metric.projected_high, metric.unit)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Trade-offs Section (if negative edges exist) */}
      {recommendation.trade_offs.length > 0 && (
        <div className="mt-3.5 rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900">
          <div className="flex items-center gap-1.5 font-semibold text-amber-800 uppercase tracking-wide text-[10px]">
            <span>⚠️</span> Ecological Trade-off to Mitigate
          </div>
          {recommendation.trade_offs.map((tradeOff) => (
            <div key={tradeOff.variable} className="mt-1">
              <p>
                <span className="font-semibold">{tradeOff.label}</span> {tradeOff.direction} by{" "}
                <span className="font-mono font-semibold">{tradeOff.magnitude}</span>.
              </p>
              {tradeOff.mitigation && (
                <p className="mt-1 text-amber-800/90 font-medium">
                  → Mitigation: {tradeOff.mitigation}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Evidence & Scientific Grounding Collapsible */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <button
          type="button"
          onClick={() => setEvidenceOpen((prev) => !prev)}
          className="flex items-center gap-1.5 text-xs font-medium text-gray-600 hover:text-[rgb(0,146,69)] transition"
        >
          <span className="rounded-full bg-[#E8F7ED] px-2 py-0.5 text-[10px] font-semibold text-[rgb(0,146,69)]">
            {recommendation.evidence.length} Evidence Sources
          </span>
          <span>{evidenceOpen ? "Hide scientific citations ↑" : "Show scientific citations ↓"}</span>
        </button>

        {evidenceOpen && (
          <ul className="mt-3 space-y-2.5 rounded-xl bg-[#F9FAFB] p-3 border border-gray-200 text-xs">
            {recommendation.evidence.map((claim) => (
              <li
                key={claim.claim_id}
                className="rounded-lg bg-white p-2.5 border border-gray-200 shadow-2xs"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-semibold text-gray-900">
                    {claim.publisher || "Academic Publication"} ({claim.year})
                  </span>
                  <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[10px] uppercase font-mono text-gray-600 border border-gray-200">
                    {claim.study_design}
                  </span>
                </div>
                <p className="mt-1 text-gray-700 italic font-medium">
                  &ldquo;{claim.document}&rdquo;
                </p>
                <p className="mt-1 text-gray-600 text-[11px] leading-relaxed">
                  {claim.summary}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

