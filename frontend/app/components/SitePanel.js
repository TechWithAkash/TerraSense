function humanizeKey(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

const PROVENANCE_LABEL = {
  user: "you told us",
  inferred: "assumed",
  fetched: "looked up",
};

export default function SitePanel({ siteState }) {
  const entries = Object.entries(siteState || {});

  return (
    <div>
      <h2 className="text-xs font-medium uppercase tracking-wide text-gray-400">Site state</h2>

      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-gray-400">Nothing known yet.</p>
      ) : (
        <ul className="mt-3 flex flex-col gap-3">
          {entries.map(([key, value]) => {
            const isTracked = value && typeof value === "object" && "value" in value;
            const displayValue = isTracked ? value.value : value;
            const provenance = isTracked ? PROVENANCE_LABEL[value.provenance] : null;

            return (
              <li key={key} className="text-sm">
                <p className="text-gray-500">{humanizeKey(key)}</p>
                <p className="text-gray-900">
                  {String(displayValue)}
                  {provenance && <span className="ml-1.5 text-xs text-gray-400">· {provenance}</span>}
                </p>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
