"use client";

import { useEffect, useRef, useState } from "react";
import { Leaf, RefreshCw, Send, Sparkles, Code2, ShieldCheck } from "lucide-react";
import { sendChatMessage } from "@/lib/api";
import RecommendationCard from "@/app/components/RecommendationCard";
import SitePanel from "@/app/components/SitePanel";

const STARTER_PROMPTS = [
  {
    title: "Degraded monoculture wheat field",
    tag: "Assignment example",
    prompt: "Soil organic carbon: 0.3%, Rainfall: low, Crop: monoculture wheat, Region: semi-arid",
  },
  {
    title: "Vague, needs clarifying questions",
    tag: "Multi-turn",
    prompt: "Biodiversity is declining on my land",
  },
  {
    title: "Falling yields, disappearing pollinators",
    tag: "Multi-metric",
    prompt: "My wheat yields keep dropping and I barely see bees anymore.",
  },
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
  const scrollAnchorRef = useRef(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  function resetConversation() {
    setMessages([]);
    setInput("");
    setSessionId(null);
    setSiteState({});
    setRecommendations([]);
    setError(null);
  }

  async function submitMessage(overrideText) {
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;

    setError(null);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");

    try {
      const payload = jsonMode
        ? { sessionId, structuredInput: JSON.parse(text) }
        : { sessionId, message: text };

      const data = await sendChatMessage(payload);
      setSessionId(data.session_id);
      setSiteState(data.site_state || {});
      setRecommendations(data.recommendations || []);
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setError(jsonMode && err instanceof SyntaxError ? "That's not valid JSON — check the syntax and try again." : err.message);
    } finally {
      setLoading(false);
    }
  }

  const hasConversation = messages.length > 0;

  return (
    <div className="mx-auto flex h-screen w-full max-w-7xl flex-col gap-4 p-3 sm:p-5">
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-3.5 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-400 text-slate-950 shadow-lg shadow-emerald-500/20">
            <Leaf className="h-5 w-5" strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white sm:text-lg">TerraSense</h1>
            <p className="hidden text-xs text-slate-400 sm:block">
              AI environmental scientist for land restoration &amp; biodiversity intelligence
            </p>
          </div>
        </div>

        <button
          onClick={resetConversation}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-emerald-500/40 hover:text-emerald-300"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          New consultation
        </button>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl">
          <div className="flex-1 overflow-y-auto">
            {!hasConversation ? (
              <div className="flex h-full flex-col items-center justify-center gap-6 px-6 py-10 text-center">
                <div>
                  <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-300">
                    <Sparkles className="h-6 w-6" />
                  </div>
                  <h2 className="text-lg font-semibold text-white">Tell me about your land</h2>
                  <p className="mx-auto mt-1.5 max-w-sm text-sm text-slate-400">
                    Describe it in your own words, paste structured data, or try one of these.
                  </p>
                </div>

                <div className="grid w-full max-w-lg gap-2.5">
                  {STARTER_PROMPTS.map((item) => (
                    <button
                      key={item.title}
                      onClick={() => submitMessage(item.prompt)}
                      className="group flex flex-col gap-1 rounded-xl border border-white/10 bg-white/[0.03] p-3.5 text-left transition hover:border-emerald-500/40 hover:bg-emerald-500/[0.06]"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-slate-200 group-hover:text-emerald-300">
                          {item.title}
                        </span>
                        <span className="shrink-0 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-400">
                          {item.tag}
                        </span>
                      </div>
                      <span className="text-xs italic text-slate-500">&ldquo;{item.prompt}&rdquo;</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4 p-4 sm:p-5">
                {messages.map((message, index) => (
                  <ChatBubble key={index} role={message.role} content={message.content} />
                ))}

                {loading && (
                  <div className="flex items-center gap-2.5 animate-fade-in-up">
                    <Avatar />
                    <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-white/10 bg-white/5 px-4 py-2.5 text-xs text-slate-400">
                      <span className="flex gap-1">
                        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-400 [animation-delay:-0.3s]" />
                        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-400 [animation-delay:-0.15s]" />
                        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-400" />
                      </span>
                      reasoning through the causal graph…
                    </div>
                  </div>
                )}

                {error && (
                  <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-2.5 text-sm text-rose-300">
                    {error}
                  </div>
                )}

                <div ref={scrollAnchorRef} />
              </div>
            )}
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              submitMessage();
            }}
            className="flex items-center gap-2 border-t border-white/10 bg-black/20 p-3"
          >
            <button
              type="button"
              onClick={() => setJsonMode((prev) => !prev)}
              title="Toggle structured JSON input"
              className={`flex shrink-0 items-center gap-1.5 rounded-lg border px-2.5 py-2 text-xs font-medium transition ${
                jsonMode
                  ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-300"
                  : "border-white/10 bg-white/5 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Code2 className="h-3.5 w-3.5" />
              JSON
            </button>

            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={jsonMode ? '{"soil_organic_carbon": 0.3, "rainfall_regime": "low"}' : "Describe your land…"}
              className="min-w-0 flex-1 rounded-lg border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition focus:border-emerald-500/60 focus:bg-white/[0.07]"
            />

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="flex shrink-0 items-center gap-1.5 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Send
              <Send className="h-3.5 w-3.5" />
            </button>
          </form>
        </section>

        <aside className="flex min-h-0 flex-col gap-4 overflow-y-auto">
          <SitePanel siteState={siteState} />

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              How this works
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              Recommendations come from a hand-curated causal graph, not a language model guessing.
              The LLM only parses your input and writes the final wording — every number is computed
              and every citation is real.
            </p>
          </div>
        </aside>
      </div>

      {recommendations.length > 0 && (
        <section className="animate-fade-in-up space-y-3 overflow-y-auto rounded-2xl border border-white/10 bg-white/[0.03] p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-base font-semibold text-white">Ranked recommendations</h2>
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-300">
              {recommendations.length} generated
            </span>
          </div>
          <div className="grid gap-4">
            {recommendations.map((recommendation) => (
              <RecommendationCard key={recommendation.intervention_id} recommendation={recommendation} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function Avatar() {
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-400 text-[10px] font-bold text-slate-950">
      TS
    </div>
  );
}

function ChatBubble({ role, content }) {
  const isUser = role === "user";
  return (
    <div className={`flex items-end gap-2.5 animate-fade-in-up ${isUser ? "flex-row-reverse" : ""}`}>
      {!isUser && <Avatar />}
      <div
        className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "rounded-tr-sm bg-emerald-500 text-slate-950 font-medium"
            : "rounded-tl-sm border border-white/10 bg-white/5 text-slate-200"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
