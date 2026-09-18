"use client";

import { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api";
import RecommendationCard from "@/app/components/RecommendationCard";
import SitePanel from "@/app/components/SitePanel";

const STARTER_PROMPTS = [
  {
    title: "Degraded monoculture wheat field",
    prompt: "Soil organic carbon: 0.3%, Rainfall: low, Crop: monoculture wheat, Region: semi-arid",
  },
  {
    title: "Vague, needs clarifying questions",
    prompt: "Biodiversity is declining on my land",
  },
  {
    title: "Falling yields, disappearing pollinators",
    prompt: "My wheat yields keep dropping and I barely see bees anymore.",
  },
];

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
      <path d="M12 19V5M12 5L6 11M12 5L18 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
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
    <div className="flex h-screen bg-white">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
          <span className="text-sm font-medium text-gray-900">TerraSense</span>
          <button onClick={resetConversation} className="text-xs text-gray-400 hover:text-gray-700">
            New consultation
          </button>
        </header>

        <div className="flex-1 overflow-y-auto">
          {!hasConversation ? (
            <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center px-4 text-center">
              <h1 className="text-2xl font-semibold text-gray-900">Tell me about your land</h1>
              <p className="mt-2 text-sm text-gray-500">
                Describe it in your own words, paste structured data, or try an example.
              </p>

              <div className="mt-8 grid w-full gap-2 sm:grid-cols-3">
                {STARTER_PROMPTS.map((item) => (
                  <button
                    key={item.title}
                    onClick={() => submitMessage(item.prompt)}
                    className="rounded-xl border border-gray-200 p-3.5 text-left text-sm text-gray-700 transition hover:border-gray-300 hover:bg-gray-50"
                  >
                    {item.title}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-6">
              {messages.map((message, index) => (
                <ChatTurn key={index} message={message} />
              ))}

              {loading && (
                <div className="flex gap-1.5 px-0.5 py-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-300 [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-300 [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-300" />
                </div>
              )}

              {error && <p className="text-sm text-red-600">{error}</p>}

              <div ref={scrollAnchorRef} />
            </div>
          )}
        </div>

        <div className="border-t border-gray-100 px-4 py-4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              submitMessage();
            }}
            className="mx-auto flex max-w-2xl items-end gap-2 rounded-3xl border border-gray-200 bg-white px-4 py-2.5 shadow-sm focus-within:border-gray-300"
          >
            <button
              type="button"
              onClick={() => setJsonMode((prev) => !prev)}
              title="Structured JSON input"
              className={`mb-1.5 shrink-0 rounded-md px-1.5 py-0.5 font-mono text-xs ${
                jsonMode ? "bg-gray-900 text-white" : "text-gray-400 hover:bg-gray-100"
              }`}
            >
              {"{ }"}
            </button>
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={jsonMode ? '{"soil_organic_carbon": 0.3}' : "Describe your land…"}
              className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-[15px] text-gray-900 placeholder-gray-400 outline-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-900 text-white transition disabled:bg-gray-200 disabled:text-gray-400"
            >
              <SendIcon />
            </button>
          </form>
        </div>
      </div>

      <aside className="hidden w-64 shrink-0 overflow-y-auto border-l border-gray-100 p-4 lg:block">
        <SitePanel siteState={siteState} />
      </aside>
    </div>
  );
}

function ChatTurn({ message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl bg-gray-100 px-4 py-2.5 text-[15px] text-gray-900">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-900 text-[10px] font-semibold text-white">
        T
      </div>
      <div className="min-w-0 flex-1">
        <p className="whitespace-pre-wrap text-[15px] leading-7 text-gray-800">{message.content}</p>
        {message.recommendations?.length > 0 && (
          <div className="mt-3 flex flex-col gap-3">
            {message.recommendations.map((recommendation) => (
              <RecommendationCard key={recommendation.intervention_id} recommendation={recommendation} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
