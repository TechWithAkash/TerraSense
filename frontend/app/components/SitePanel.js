function humanizeKey(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

const PROVENANCE_STYLES = {
  user: {
    label: "You told us",
    badge: "bg-[#E8F7ED] text-[rgb(0,146,69)] border-[rgba(0,146,69,0.25)]",
  },
  inferred: {
    label: "Assumed",
    badge: "bg-amber-50 text-amber-800 border-amber-200",
  },
  fetched: {
    label: "Looked up",
    badge: "bg-sky-50 text-sky-800 border-sky-200",
  },
};

export default function SitePanel({ siteState }) {
  const entries = Object.entries(siteState || {});

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-900">
            Site Environmental State
          </h3>
          <p className="text-[11px] text-gray-500 font-mono">12 Ecological Metrics</p>
        </div>
        <span className="flex h-2 w-2 rounded-full bg-[rgb(0,146,69)]" />
      </div>

      {entries.length === 0 ? (
        <div className="py-6 text-center">
          <p className="text-xs text-gray-500">No site metrics recorded yet.</p>
          <p className="mt-1 text-[11px] text-gray-400">
            Describe your land or pick a sample scenario to populate the baseline state.
          </p>
        </div>
      ) : (
        <ul className="mt-3 divide-y divide-gray-100">
          {entries.map(([key, value]) => {
            const isTracked = value && typeof value === "object" && "value" in value;
            const displayValue = isTracked ? value.value : value;
            const provenance = isTracked ? PROVENANCE_STYLES[value.provenance] : null;

            return (
              <li key={key} className="flex items-center justify-between py-2 text-xs">
                <span className="text-gray-600 font-medium">{humanizeKey(key)}</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-gray-900">
                    {String(displayValue)}
                  </span>
                  {provenance && (
                    <span
                      className={`rounded-full border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${provenance.badge}`}
                    >
                      {provenance.label}
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

