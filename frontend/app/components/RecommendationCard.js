const CONFIDENCE_COLORS = {
  High: "bg-emerald-100 text-emerald-800",
  "Medium-High": "bg-lime-100 text-lime-800",
  Medium: "bg-amber-100 text-amber-800",
  Low: "bg-rose-100 text-rose-800",
};

const HORIZON_LABELS = {
  short_term: "Short term",
  medium_term: "Medium term",
  long_term: "Long term",
};

function formatRange(low, high, unit) {
  return `${low} → ${high} ${unit}`.trim();
}

export default function RecommendationCard({ recommendation }) {
  const confidenceColor = CONFIDENCE_COLORS[recommendation.confidence.band] || "bg-gray-100 text-gray-800";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            #{recommendation.rank} recommendation
          </span>
          <h3 className="mt-1 text-lg font-semibold text-gray-900">{recommendation.what_to_do}</h3>
        </div>
        <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${confidenceColor}`}>
          {recommendation.confidence.band} confidence ({recommendation.confidence.score})
        </span>
      </div>

      <p className="mt-3 text-sm leading-relaxed text-gray-700">{recommendation.why_it_works}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Impacted metrics</h4>
          <ul className="mt-2 space-y-1 text-sm text-gray-700">
            {recommendation.impacted_metrics.map((metric) => (
              <li key={metric.variable} className="flex justify-between gap-2">
                <span>{metric.label}</span>
                <span className="font-mono text-xs text-gray-600">
                  {formatRange(metric.projected_low, metric.projected_high, metric.unit)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-2 text-sm text-gray-700">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Time horizon</span>
            <p>{HORIZON_LABELS[recommendation.time_horizon] || recommendation.time_horizon}</p>
          </div>
          {recommendation.cost_inr_per_ha && (
            <div>
              <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Cost</span>
              <p>
                ₹{recommendation.cost_inr_per_ha[0].toLocaleString("en-IN")} – ₹
                {recommendation.cost_inr_per_ha[1].toLocaleString("en-IN")} / hectare
              </p>
            </div>
          )}
        </div>
      </div>

      {recommendation.trade_offs.length > 0 && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-amber-800">Trade-off to weigh</h4>
          {recommendation.trade_offs.map((tradeOff) => (
            <div key={tradeOff.variable} className="mt-1 text-sm text-amber-900">
              <p>
                {tradeOff.label} {tradeOff.direction} by {tradeOff.magnitude}.
              </p>
              {tradeOff.mitigation && <p className="mt-1 text-xs italic">Mitigation: {tradeOff.mitigation}</p>}
            </div>
          ))}
        </div>
      )}

      <details className="mt-4">
        <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-gray-500">
          Evidence ({recommendation.evidence.length} sources)
        </summary>
        <ul className="mt-2 space-y-2 text-xs text-gray-600">
          {recommendation.evidence.map((claim) => (
            <li key={claim.claim_id} className="border-l-2 border-gray-200 pl-2">
              <span className="font-medium text-gray-800">
                {claim.document} ({claim.year})
              </span>
              <span className="ml-1 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] uppercase">{claim.study_design}</span>
              <p className="mt-0.5">{claim.summary}</p>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
