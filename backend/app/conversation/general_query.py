from app.knowledge.search import get_chunk_index
from app.llm.client import complete

# handles the case the site-intake pipeline can't: a user asking the system a direct question
# ("what does your knowledge base say about X") instead of describing their land.
# without this, a question with nothing extractable from it just looped the same clarifying
# question forever, which reads as broken. answering it, grounded in the same chunk store the
# reasoning engine cites from, is what actually demonstrates the retrieval layer working.

_QUESTION_STARTERS = (
    "what",
    "how",
    "why",
    "does",
    "do",
    "is",
    "are",
    "can",
    "could",
    "should",
    "which",
    "who",
    "when",
    "where",
    "will",
    "would",
    "tell me",
    "explain",
)

_SYSTEM_PROMPT = (
    "You answer questions about an environmental knowledge base using ONLY the excerpts provided "
    "below. Do not invent facts, numbers, or sources beyond what is given. If the excerpts do not "
    "cover the question, say so plainly. Keep the answer to 3-4 sentences, and name the source(s) "
    "you drew from."
)


def is_general_question(text: str) -> bool:
    stripped = text.strip().lower()
    if not stripped:
        return False
    if "?" in stripped:
        return True
    return stripped.startswith(_QUESTION_STARTERS)


def answer_general_question(text: str) -> str:
    chunks = get_chunk_index().search(text, top_k=4)
    if not chunks:
        return (
            "I don't have anything in my knowledge base that directly answers that. "
            "I'm built to reason about a specific piece of land, though — try describing yours: "
            "soil condition, rainfall, crop, or land use, and I'll take it from there."
        )

    excerpt_block = "\n\n".join(f"[{chunk.title}]\n{chunk.content}" for chunk in chunks)
    llm_answer = complete(_SYSTEM_PROMPT, f"Question: {text}\n\nExcerpts:\n{excerpt_block}")
    if llm_answer:
        return llm_answer.strip()

    # rule-based fallback with no LLM key configured: quote the best-matching excerpts from up
    # to two distinct sources directly, which is honest and still grounded, just less fluent
    seen_titles: set[str] = set()
    quotes: list[str] = []
    for chunk in chunks:
        if chunk.title in seen_titles:
            continue
        seen_titles.add(chunk.title)
        quoted = chunk.content[:350].rstrip()
        ellipsis = "…" if len(chunk.content) > 350 else ""
        quotes.append(f"From {chunk.title}: {quoted}{ellipsis}")
        if len(quotes) == 2:
            break

    return "\n\n".join(quotes) + (
        "\n\nTell me about your specific land and I can turn this into a tailored recommendation."
    )
