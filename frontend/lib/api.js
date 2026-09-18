const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// free hosting (Render's free tier, in particular) puts the backend to sleep after a period of
// no traffic, so the very first request after a gap can take well over 30s just to wake the
// container - measured this directly against the deployed backend, a cold request timed out at
// 30s with nothing back yet, so the margin here is deliberately generous rather than a guess.
// nothing is actually wrong when this happens, it just needs patience instead of hanging forever
// or failing fast with a confusing error.
const REQUEST_TIMEOUT_MS = 120_000;

async function fetchWithTimeout(url, options) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(
        "The server is taking longer than expected to respond. It may be waking up from sleep on free hosting - please try again in a moment."
      );
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

// fire-and-forget: call this as soon as the page loads so a sleeping backend starts waking up
// in the background, before the user finishes typing their first message
export function warmUpBackend() {
  fetch(`${API_BASE}/healthz`).catch(() => {});
}

export async function sendChatMessage({ sessionId, message, structuredInput }) {
  const response = await fetchWithTimeout(`${API_BASE}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId ?? null,
      message: message ?? null,
      structured_input: structuredInput ?? null,
    }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(detail.detail || "Something went wrong talking to TerraSense.");
  }

  return response.json();
}
