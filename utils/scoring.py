from __future__ import annotations

from typing import Dict


def calculate_score(responses: Dict[str, int]) -> int:
    return sum(int(v) for v in responses.values())


def calculate_subscores(responses: Dict[str, int]) -> Dict[str, int]:
    groups = {
        "Pilotage et visibilité": ["q1", "q2", "q4", "q6"],
        "Charge opérationnelle": ["q3", "q5", "q9"],
        "Risque organisationnel": ["q7", "q8", "q10"],
    }
    return {name: sum(int(responses.get(q, 0)) for q in keys) for name, keys in groups.items()}


def determine_band(score: int) -> str:
    if score <= 6:
        return "🟢 Maîtrisé"
    if score <= 14:
        return "🟠 Sous tension"
    return "🔴 Risque structurel"


def get_top_leaks(subscores: Dict[str, int]) -> list[str]:
    ordered = sorted(subscores.items(), key=lambda item: item[1], reverse=True)
    return [name for name, _ in ordered[:3]]
