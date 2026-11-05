import re
from typing import List

_FOLLOWUP = re.compile(
    r"\b(it|that|this|those|these|they|them|he|she|his|her|above|previous|earlier|same)\b",
    re.IGNORECASE,
)


def looks_like_followup(question: str) -> bool:
    words = (question or "").strip().split()
    if len(words) <= 4:
        return True
    return bool(_FOLLOWUP.search(question or ""))


def history_without_current_question(history: list, question: str) -> list:
    """Drop the turn we just saved so the model does not see the question twice."""
    if not history:
        return []
    last = history[-1]
    if last.get("role") == "user" and last.get("content") == question:
        return history[:-1]
    return list(history)


def citation_label(metadata: dict) -> str:
    source = (metadata or {}).get("source") or "Unknown"
    page = (metadata or {}).get("page")
    if isinstance(page, float) and page.is_integer():
        page = int(page)
    if isinstance(page, int) and page > 0:
        return f"{source} (page {page})"
    return str(source)


def citation_labels(docs) -> List[str]:
    labels = []
    for doc in docs:
        label = citation_label(getattr(doc, "metadata", {}) or {})
        if label not in labels:
            labels.append(label)
    return labels


def append_sources(answer: str, labels: List[str]) -> str:
    if not labels:
        return answer
    lines = [answer.rstrip(), ""]
    for label in labels:
        if label.startswith("http://") or label.startswith("https://"):
            lines.append(f"* Source: [{label}]({label})")
        else:
            lines.append(f"* Source: {label}")
    return "\n".join(lines) + "\n"


def message_text(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text") or ""))
        return "\n".join(part for part in parts if part).strip()
    return str(content).strip()


def answer_was_not_found(answer: str) -> bool:
    return "not found" in (answer or "").lower()
