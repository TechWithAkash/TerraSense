const PROVENANCE_STYLES = {
  user: { label: "You told us", color: "bg-emerald-100 text-emerald-800" },
  inferred: { label: "Assumed", color: "bg-amber-100 text-amber-800" },
  fetched: { label: "Looked up", color: "bg-sky-100 text-sky-800" },
};

function humanizeKey(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function SitePanel({ siteState }) {
  const entries = Object.entries(siteState || {});

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-500">
        Nothing known about the site yet. Start describing your land in the chat.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Site state</h3>
      <ul className="mt-3 space-y-2 text-sm">
        {entries.map(([key, value]) => {
          const isTracked = value && typeof value === "object" && "value" in value;
          const displayValue = isTracked ? value.value : value;
          const provenance = isTracked ? PROVENANCE_STYLES[value.provenance] : null;

          return (
            <li key={key} className="flex items-center justify-between gap-2">
              <span className="text-gray-700">{humanizeKey(key)}</span>
              <span className="flex items-center gap-2">
                <span className="font-mono text-xs text-gray-800">{String(displayValue)}</span>
                {provenance && (
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${provenance.color}`}>
                    {provenance.label}
                  </span>
                )}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
