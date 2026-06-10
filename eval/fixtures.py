"""Pre-recorded responses for offline benchmark dry-run mode."""

from __future__ import annotations

from eval.scenarios import ALL_SCENARIOS

# Per-scenario fixture responses — last item is scored against expected_outcomes.
FIXTURE_RESPONSES: dict[str, dict[str, list[str]]] = {
    "pref_recall_1": {
        "with_memory": [
            "Got it — I'll remember you prefer Python for backend work.",
            "Based on your preference, Python is the best choice for the API.",
        ],
        "without_memory": [
            "Noted.",
            "You could use Python or JavaScript depending on your team.",
        ],
    },
    "pref_recall_2": {
        "with_memory": [
            "I'll keep comments minimal as you prefer.",
            "I'll keep comments minimal and only explain complex logic.",
        ],
        "without_memory": [
            "Understood.",
            "Here is a detailed review with extensive comments on every line.",
        ],
    },
    "contradiction_1": {
        "with_memory": [
            "Express noted.",
            "Fastify noted — I've updated your stack preference.",
            "We are using Fastify now for the backend.",
        ],
        "without_memory": [
            "Express is common.",
            "Fastify is also an option.",
            "Express is a common choice; which framework do you use?",
        ],
    },
    "forgetting_1": {
        "with_memory": [
            "Vue is optional — I won't store that as a firm preference.",
            "I don't have a confirmed frontend framework preference stored.",
        ],
        "without_memory": [
            "Vue could work.",
            "Vue is one option among many frontend frameworks.",
        ],
    },
    "context_5": {
        "with_memory": [
            "Ruby could work, but I don't see a stored preference for it.",
        ],
        "without_memory": [
            "Which language are you considering — Ruby, Python, or something else?",
        ],
    },
}

FIXTURE_MEMORY_DUMPS: dict[str, str] = {
    "pref_recall_1": "backend_language → prefers → python",
    "pref_recall_2": "code_style → prefers → minimal_comments",
    "contradiction_1": "backend_framework → prefers → fastify",
    "forgetting_1": "",
    "context_5": "",
}

for scenario in ALL_SCENARIOS:
    if scenario.id in FIXTURE_RESPONSES:
        continue
    FIXTURE_RESPONSES[scenario.id] = {
        "with_memory": [
            "Setup acknowledged with memory context.",
            "Memory-informed response for demo.",
        ],
        "without_memory": [
            "Setup acknowledged.",
            "Generic response without memory context.",
        ],
    }
