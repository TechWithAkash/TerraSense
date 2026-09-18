"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { sendChatMessage } from "@/lib/api";
import RecommendationCard from "@/app/components/RecommendationCard";
import SitePanel from "@/app/components/SitePanel";

const STARTER_PROMPTS = [
  {
    title: "Degraded monoculture wheat field",
    badge: "Semi-arid AEZ",
    prompt: "Soil organic carbon: 0.3%, Rainfall: low, Crop: monoculture wheat, Region: semi-arid",
  },
  {
    title: "Vague input (Clarification flow)",
    badge: "Gap analysis",
    prompt: "Biodiversity is declining on my land",
  },
  {
    title: "Falling yields & pollinator loss",
    badge: "Multi-variable",
    prompt: "My wheat yields keep dropping and I barely see bees anymore.",
  },
];

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
      <path
        d="M12 19V5M12 5L6 11M12 5L18 11"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LeafIcon({ className = "h-4 w-4" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5c0 3.5 3.5 6.5 7 6.5 1.5 0 3-.5 4.5-1.5 1.5-1 3.5-3.5 3.5-10.5z" />
    </svg>
  );
}

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [siteState, setSiteState] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jsonMode, setJsonMode] = useState(false);
  const scrollAnchorRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages, loading]);

  function resetConversation() {
    setMessages([]);
    setInput("");
    setSessionId(null);
    setSiteState({});
    setError(null);
  }

  async function submitMessage(overrideText) {
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;

    setError(null);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    try {
      const payload = jsonMode
        ? { sessionId, structuredInput: JSON.parse(text) }
        : { sessionId, message: text };

      const data = await sendChatMessage(payload);
      setSessionId(data.session_id);
      setSiteState(data.site_state || {});
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply, recommendations: data.recommendations || [] },
      ]);
    } catch (err) {
      setError(jsonMode && err instanceof SyntaxError ? "That's not valid JSON." : err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleInputChange(event) {
    setInput(event.target.value);
    const el = event.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submitMessage();
    }
  }

  const hasConversation = messages.length > 0;

  return (
    <div className="flex h-screen flex-col bg-[#F9FAFB] text-[#000000]">
      {/* Header aligned with Darukaa Earth branding */}
      <header className="flex shrink-0 items-center justify-between border-b border-gray-200 bg-white/85 px-4 py-3 backdrop-blur-md sm:px-6">
        <div className="flex items-center gap-3">
          <Image
            src="/darukaa-logo.png"
            alt="Darukaa.earth Logo"
            width={160}
            height={26}
            className="h-6 w-auto object-contain"
            priority
          />
          <span className="hidden h-4 w-px bg-gray-300 sm:block" />
          <div className="hidden sm:flex items-center gap-2">
            <span className="rounded-full bg-[#E8F7ED] px-2.5 py-0.5 text-[10px] font-semibold text-[rgb(0,146,69)] border border-[rgba(0,146,69,0.25)]">
              TerraSense
            </span>
            <span className="text-[11px] text-gray-500 font-mono hidden md:inline">
              Nature Intelligence Platform
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="hidden items-center gap-1.5 text-xs text-gray-500 sm:flex">
            <span className="h-2 w-2 rounded-full bg-[rgb(0,146,69)] animate-pulse" />
            Causal Reasoning Active
          </span>
          <button
            onClick={resetConversation}
            className="rounded-full border border-gray-200 bg-[#F3F4F6] px-3 py-1 text-xs font-medium text-gray-700 transition hover:border-[rgb(0,146,69)] hover:text-[#000000]"
          >
            New Consultation
          </button>
        </div>
      </header>

      <div className="mx-auto flex min-h-0 w-full max-w-6xl flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex-1 overflow-y-auto">
            {!hasConversation ? (
              <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center px-4 py-8 text-center">
                <div className="mb-4">
                  <Image
                    src="/darukaa-logo.png"
                    alt="Darukaa.earth"
                    width={220}
                    height={34}
                    className="mx-auto h-8 w-auto object-contain"
                    priority
                  />
                </div>

                <div className="inline-flex items-center gap-2 rounded-full bg-[#E8F7ED] px-3.5 py-1 text-xs font-semibold text-[rgb(0,146,69)] border border-[rgba(0,146,69,0.3)]">
                  <LeafIcon className="h-3.5 w-3.5" />
                  AI Environmental Scientist • TerraSense
                </div>

                <h1 className="mt-4 text-3xl font-semibold tracking-[-0.72px] text-[#000000] sm:text-4xl">
                  Nature Intelligence & Biodiversity Reasoning
                </h1>
                <p className="mt-3 max-w-lg text-sm text-gray-600">
                  Describe your land condition, soil organic carbon, or rainfall regime. TerraSense
                  evaluates multi-variable causal interactions and grounds every recommendation in
                  peer-reviewed research.
                </p>

                <div className="mt-8 grid w-full gap-3 sm:grid-cols-3">
                  {STARTER_PROMPTS.map((item) => (
                    <button
                      key={item.title}
                      onClick={() => submitMessage(item.prompt)}
                      className="group flex flex-col justify-between rounded-2xl border border-gray-200 bg-[#F3F4F6] p-4 text-left transition hover:border-[rgb(0,146,69)] hover:bg-white hover:shadow-md"
                      style={{ transitionDuration: "300ms", transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)" }}
                    >
                      <div>
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(0,146,69)]">
                          {item.badge}
                        </span>
                        <h3 className="mt-1 text-sm font-semibold text-gray-900 group-hover:text-[rgb(0,146,69)]">
                          {item.title}
                        </h3>
                      </div>
                      <p className="mt-2 text-xs text-gray-500 line-clamp-2">{item.prompt}</p>
                    </button>
                  ))}
                </div>

                <div className="mt-8 flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-[rgb(0,146,69)]" />
                    Multi-Variable Causal Graph
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-[rgb(0,146,69)]" />
                    FAO & IPCC Grounded
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-[rgb(0,146,69)]" />
                    Zero Generic Advice
                  </span>
                </div>
              </div>
            ) : (
              <div className="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-6">
                {messages.map((message, index) => (
                  <ChatTurn key={index} message={message} />
                ))}

                {loading && (
                  <div className="flex items-center gap-2 rounded-xl bg-white border border-gray-200 px-4 py-3 shadow-sm text-xs text-gray-600">
                    <span className="h-2 w-2 rounded-full bg-[rgb(0,146,69)] animate-pulse" />
                    <span>Propagating causal graph & retrieving peer-reviewed evidence…</span>
                  </div>
                )}

                {error && (
                  <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                    {error}
                  </div>
                )}

                <div ref={scrollAnchorRef} />
              </div>
            )}
          </div>

          {/* Prompt input area */}
          <div className="border-t border-gray-200 bg-white/90 px-4 py-4 backdrop-blur-sm">
            <form
              onSubmit={(event) => {
                event.preventDefault();
                submitMessage();
              }}
              className="mx-auto flex max-w-2xl items-end gap-2 rounded-2xl border border-gray-200 bg-[#F9FAFB] p-2.5 shadow-sm transition focus-within:border-[rgb(0,146,69)] focus-within:bg-white focus-within:ring-2 focus-within:ring-[rgba(0,146,69,0.15)]"
              style={{ transitionDuration: "300ms", transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)" }}
            >
              <button
                type="button"
                onClick={() => setJsonMode((prev) => !prev)}
                title="Toggle structured JSON input mode"
                className={`mb-1 shrink-0 rounded-lg px-2 py-1 font-mono text-xs font-semibold transition ${
                  jsonMode
                    ? "bg-[#0B1F16] text-[rgb(0,146,69)] border border-[rgb(0,146,69)]"
                    : "bg-white text-gray-600 border border-gray-200 hover:border-gray-300"
                }`}
              >
                {"{ }"} JSON
              </button>
              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  jsonMode
                    ? '{"soil_organic_carbon": 0.3, "land_cover": "cropland", "rainfall_regime": "low"}'
                    : "Describe your land condition, soil organic carbon %, or rainfall pattern…"
                }
                className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-[15px] text-[#000000] placeholder-gray-400 outline-none"
                data-gramm="false"
                data-gramm_editor="false"
                data-enable-grammarly="false"
                autoComplete="off"
                spellCheck="false"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                aria-label="Send message"
                className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#0B1F16] text-white transition hover:bg-[rgb(0,146,69)] disabled:bg-gray-200 disabled:text-gray-400 shadow-sm"
                style={{ transitionDuration: "250ms", transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)" }}
              >
                <SendIcon />
              </button>
            </form>
          </div>
        </div>

        {/* Sidebar displaying Site State */}
        <aside className="hidden w-72 shrink-0 overflow-y-auto border-l border-gray-200 bg-[#F3F4F6]/50 p-4 lg:block">
          <SitePanel siteState={siteState} />
        </aside>
      </div>
    </div>
  );
}

function ChatTurn({ message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl bg-[#0B1F16] px-4 py-2.5 text-[15px] text-white shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-[rgb(0,146,69)] text-white shadow-sm">
        <LeafIcon className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="whitespace-pre-wrap text-[15px] leading-7 text-gray-800">{message.content}</p>
        </div>
        {message.recommendations?.length > 0 && (
          <div className="mt-4 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[rgb(0,146,69)]" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[rgb(0,146,69)]">
                Ranked Ecological Interventions
              </h3>
            </div>
            {message.recommendations.map((recommendation) => (
              <RecommendationCard
                key={recommendation.intervention_id}
                recommendation={recommendation}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

