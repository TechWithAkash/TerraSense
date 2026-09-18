"use client";

import { useState } from "react";

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

  return (
    <div className="rounded-xl border border-gray-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-medium text-gray-900">
          {recommendation.rank}. {recommendation.what_to_do}
        </h3>
        <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
          {recommendation.confidence.band} · {Math.round(recommendation.confidence.score * 100)}%
        </span>
      </div>

      <p className="mt-1.5 text-sm leading-relaxed text-gray-600">{recommendation.why_it_works}</p>

      <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
        {recommendation.impacted_metrics.map((metric) => (
          <div key={metric.variable} className="flex items-baseline gap-1.5">
            <dt className="text-gray-400">{metric.label}</dt>
            <dd className="font-mono text-xs text-emerald-600">
              {formatRange(metric.projected_low, metric.projected_high, metric.unit)}
            </dd>
          </div>
        ))}
      </dl>

      <p className="mt-2 text-xs text-gray-400">
        {HORIZON_LABELS[recommendation.time_horizon] || recommendation.time_horizon}
        {recommendation.cost_inr_per_ha && (
          <>
            {" · "}₹{recommendation.cost_inr_per_ha[0].toLocaleString("en-IN")}–₹
            {recommendation.cost_inr_per_ha[1].toLocaleString("en-IN")} / ha
          </>
        )}
      </p>

      {recommendation.trade_offs.length > 0 && (
        <div className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {recommendation.trade_offs.map((tradeOff) => (
            <p key={tradeOff.variable}>
              {tradeOff.label} {tradeOff.direction} by {tradeOff.magnitude}.
              {tradeOff.mitigation && <span className="text-amber-700"> {tradeOff.mitigation}</span>}
            </p>
          ))}
        </div>
      )}

      <button
        onClick={() => setEvidenceOpen((prev) => !prev)}
        className="mt-3 text-xs text-gray-400 hover:text-gray-700"
      >
        {evidenceOpen ? "Hide" : "Show"} evidence ({recommendation.evidence.length})
      </button>

      {evidenceOpen && (
        <ul className="mt-2 flex flex-col gap-1.5">
          {recommendation.evidence.map((claim) => (
            <li key={claim.claim_id} className="text-xs text-gray-500">
              <span className="text-gray-700">
                {claim.document} ({claim.year})
              </span>{" "}
              — {claim.summary}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
