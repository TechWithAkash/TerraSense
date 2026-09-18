"use client";

import { useState } from "react";
import { sendChatMessage } from "@/lib/api";
import RecommendationCard from "@/app/components/RecommendationCard";
import SitePanel from "@/app/components/SitePanel";

const STARTER_PROMPTS = [
  "Biodiversity is declining on my land",
  "Soil organic carbon: 0.3%, Rainfall: low, Crop: monoculture wheat, Region: semi-arid",
  "My wheat yields keep dropping and I barely see bees anymore.",
];

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [siteState, setSiteState] = useState({});
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jsonMode, setJsonMode] = useState(false);

  async function submitMessage(text) {
    if (!text.trim() || loading) return;
    setError(null);
    setLoading(true);

    const userTurn = { role: "user", content: text };
    setMessages((prev) => [...prev, userTurn]);
    setInput("");

    try {
      let payload = { sessionId, message: text };

      if (jsonMode) {
        const parsed = JSON.parse(text); // let a bad JSON payload surface as a visible error, not a silent failure
        payload = { sessionId, structuredInput: parsed };
      }

      const data = await sendChatMessage(payload);
      setSessionId(data.session_id);
      setSiteState(data.site_state);
      setRecommendations(data.recommendations || []);
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-4 px-4 py-6">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">TerraSense</h1>
        <p className="text-sm text-gray-600">
          An AI environmental scientist for land restoration and biodiversity intelligence.
        </p>
      </header>

      <div className="grid flex-1 gap-4 md:grid-cols-[2fr_1fr]">
        <section className="flex flex-col rounded-xl border border-gray-200 bg-gray-50">
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.length === 0 && (
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Try one of these, or describe your own land:</p>
                {STARTER_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => submitMessage(prompt)}
                    className="block w-full rounded-lg border border-gray-200 bg-white p-3 text-left text-sm text-gray-700 hover:border-emerald-400 hover:bg-emerald-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`max-w-[85%] rounded-lg p-3 text-sm ${
                  message.role === "user"
                    ? "ml-auto bg-emerald-600 text-white"
                    : "bg-white text-gray-800 shadow-sm"
                }`}
              >
                {message.content}
              </div>
            ))}

            {loading && <div className="text-xs text-gray-400">TerraSense is thinking…</div>}
            {error && <div className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              submitMessage(input);
            }}
            className="flex gap-2 border-t border-gray-200 p-3"
          >
            <label className="flex items-center gap-1 text-xs text-gray-500">
              <input type="checkbox" checked={jsonMode} onChange={(event) => setJsonMode(event.target.checked)} />
              JSON
            </label>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={jsonMode ? '{"soil_organic_carbon": 0.3, "rainfall_regime": "low"}' : "Describe your land…"}
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </section>

        <aside className="flex flex-col gap-4">
          <SitePanel siteState={siteState} />
        </aside>
      </div>

      {recommendations.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Ranked recommendations</h2>
          {recommendations.map((recommendation) => (
            <RecommendationCard key={recommendation.intervention_id} recommendation={recommendation} />
          ))}
        </section>
      )}
    </div>
  );
}
