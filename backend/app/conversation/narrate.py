import re

from app.llm.client import complete

# writes the human-readable explanation. the numbers are never invented here - they are computed
# upstream by the reasoning engine and just get put into words. an LLM pass may rephrase for
# readability, but only if every number it writes can be traced back to the numbers we gave it.

_NUMBER_PATTERN = re.compile(r"-?\d+\.?\d*")


def _format_range(low: float, mid: float, high: float, unit: str) -> str:
    return f"{low:+.2f} to {high:+.2f} {unit} (typical {mid:+.2f})"


def build_why_it_works(
    intervention_label: str, path_steps: list[dict], claim_summaries: list[str]
) -> str:
    if not path_steps:
        return f"{intervention_label} is expected to directly improve the site based on the cited evidence."

    direct_targets: list[str] = []
    downstream_targets: list[str] = []
    seen: set[str] = set()
    for step in path_steps:
        if step["to_label"] in seen:
            continue  # multiple causal paths can converge on the same variable, only say it once
        seen.add(step["to_label"])
        if step["from_variable"] == "intervention":
            direct_targets.append(step["to_label"])
        else:
            downstream_targets.append(step["to_label"])

    chain = f"{intervention_label} directly improves {', '.join(direct_targets)}."
    if downstream_targets:
        chain += f" That in turn raises {', '.join(downstream_targets)}."

    evidence_sentence = ""
    if claim_summaries:
        evidence_sentence = " " + " ".join(claim_summaries[:2])
    return chain + evidence_sentence


def _numbers_in(text: str) -> set[str]:
    return set(_NUMBER_PATTERN.findall(text))


def polish_with_verification(draft_text: str, grounded_numbers: set[str]) -> str:
    # ask the LLM to rewrite more naturally, but reject the rewrite if it introduces a number
    # that wasn't in the grounded set - that's exactly the failure mode a naive chatbot has
    system_prompt = (
        "Rewrite the following explanation in clear, plain English for a farmer or land manager. "
        "Keep every number exactly as given. Do not add any new number, percentage, or statistic "
        "that is not already present in the text. Keep it to 2-3 sentences."
    )
    polished = complete(system_prompt, draft_text)
    if not polished:
        return draft_text

    polished_numbers = _numbers_in(polished)
    if not polished_numbers.issubset(grounded_numbers | _numbers_in(draft_text)):
        return draft_text  # the rewrite introduced an unsupported number, reject it and keep the safe draft

    return polished


def build_chat_reply(
    recommendation_count: int, clarifying_question: str | None, top_label: str | None
) -> str:
    if clarifying_question:
        return clarifying_question
    if recommendation_count == 0:
        return "I couldn't find an intervention that fits what you've told me yet. Could you share a bit more about the land?"
    if recommendation_count == 1:
        return f"Based on what you've told me, here's my top recommendation: {top_label}."
    return f"Based on what you've told me, here are {recommendation_count} ranked recommendations, starting with {top_label}."
