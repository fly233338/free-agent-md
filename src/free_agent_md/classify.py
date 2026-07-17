from __future__ import annotations

import re

from .settings import CategoryRule


def classify_repository(
    full_name: str,
    description: str | None,
    language: str | None,
    topics: list[str],
    rules: list[CategoryRule],
    overrides: dict[str, str],
) -> str:
    override = overrides.get(full_name.lower())
    if override:
        return override

    text = f"{full_name} {description or ''}".lower()
    words = set(re.findall(r"[a-z0-9+#.-]+", text))
    topic_set = {topic.lower() for topic in topics}
    scores: list[tuple[int, str]] = []
    for rule in rules:
        score = 0
        score += 3 * len(topic_set.intersection(topic.lower() for topic in rule.topics))
        for keyword in rule.keywords:
            lowered = keyword.lower()
            if (" " in lowered and lowered in text) or lowered in words:
                score += 2
        if language and language.lower() in {item.lower() for item in rule.languages}:
            score += 1
        scores.append((score, rule.name))

    best = max((score for score, _ in scores), default=0)
    winners = [name for score, name in scores if score == best]
    threshold = next((rule.threshold for rule in rules if rule.name in winners), 3)
    if best < threshold or len(winners) != 1:
        return "Other"
    return winners[0]
