"""Benchmark scenario definitions for MnemOS evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Turn:
    """One user turn in a benchmark session."""

    user_message: str
    expected_behavior: str = ""


@dataclass
class Session:
    """Ordered turns within one session."""

    session_id: str
    turns: list[Turn]


@dataclass
class Expectation:
    """Automated scoring expectation for a scenario."""

    check_type: str
    check_value: str
    description: str = ""


@dataclass
class Scenario:
    """Full benchmark scenario definition."""

    id: str
    name: str
    description: str
    category: str
    conversations: list[Session]
    expected_outcomes: list[Expectation] = field(default_factory=list)


def _scenario(
    sid: str,
    name: str,
    category: str,
    sessions: list[tuple[str, list[tuple[str, str]]]],
    outcomes: list[tuple[str, str, str]],
) -> Scenario:
    conversations = [
        Session(session_id=s_id, turns=[Turn(user_message=m, expected_behavior=b) for m, b in turns])
        for s_id, turns in sessions
    ]
    expectations = [
        Expectation(check_type=t, check_value=v, description=d) for t, v, d in outcomes
    ]
    return Scenario(
        id=sid,
        name=name,
        description=name,
        category=category,
        conversations=conversations,
        expected_outcomes=expectations,
    )


ALL_SCENARIOS: list[Scenario] = [
    _scenario(
        "pref_recall_1",
        "Simple Preference",
        "recall",
        [
            ("s1", [("I always prefer Python over JavaScript for backend work.", "store")]),
            ("s2", [("What language should we use for the API?", "recall python")]),
        ],
        [("keyword_present", "Python", "Should mention Python from memory")],
    ),
    _scenario(
        "pref_recall_2",
        "Nested Preference",
        "recall",
        [
            ("s1", [("I like minimal code comments. Only explain complex logic.", "store")]),
            ("s2", [("Review this function for me.", "minimal comments")]),
        ],
        [("keyword_present", "comment", "Should reference comment preference")],
    ),
    _scenario(
        "contradiction_1",
        "Framework Switch",
        "contradiction",
        [
            ("s1", [("We use Express.", "store express")]),
            ("s2", [("We switched to Fastify.", "store fastify")]),
            ("s3", [("What framework are we using?", "recall fastify")]),
        ],
        [
            ("keyword_present", "Fastify", "Should use current framework"),
            ("contradiction_resolved", "express|Fastify", "Should not prefer stale Express"),
        ],
    ),
    _scenario(
        "forgetting_1",
        "Low Conviction Rejection",
        "forgetting",
        [
            ("s1", [("Maybe we should try Vue sometime.", "reject")]),
            ("s2", [("What frontend framework are we using?", "no vue")]),
        ],
        [("keyword_absent", "Vue", "Should not assert Vue preference")],
    ),
    _scenario(
        "context_5",
        "No False Memory Injection",
        "context",
        [
            ("s1", [("Should I use Ruby for this?", "no false memory")]),
        ],
        [("keyword_absent", "Ruby preference", "Must not hallucinate Ruby preference")],
    ),
]

# Extend to 25 scenarios with placeholders for remaining categories
_EXTRA = [
    ("pref_recall_3", "Tool Preference", "recall"),
    ("pref_recall_4", "Architectural Preference", "recall"),
    ("pref_recall_5", "Multiple Preferences", "recall"),
    ("contradiction_2", "Deadline Change", "contradiction"),
    ("contradiction_3", "Team Size Change", "contradiction"),
    ("contradiction_4", "Technology Correction", "contradiction"),
    ("contradiction_5", "Role Change", "contradiction"),
    ("interference_1", "Stale Tech Stack", "interference"),
    ("interference_2", "Outdated Dependency", "interference"),
    ("interference_3", "Replaced Service", "interference"),
    ("interference_4", "Changed Convention", "interference"),
    ("interference_5", "Retracted Decision", "interference"),
    ("forgetting_2", "Hedged Statement", "forgetting"),
    ("forgetting_3", "Temporal Decay", "forgetting"),
    ("forgetting_4", "Information Overload", "forgetting"),
    ("forgetting_5", "Dormant Memory UCB", "forgetting"),
    ("context_1", "10-Session Continuity", "context"),
    ("context_2", "Associative Recall", "context"),
    ("context_3", "Personalization Quality", "context"),
    ("context_4", "Project Context", "context"),
]

for sid, name, category in _EXTRA:
    ALL_SCENARIOS.append(
        Scenario(
            id=sid,
            name=name,
            description=name,
            category=category,
            conversations=[
                Session(
                    session_id="s1",
                    turns=[Turn(user_message=f"Benchmark setup for {name}", expected_behavior="setup")],
                ),
                Session(
                    session_id="s2",
                    turns=[Turn(user_message=f"Verify {name} behavior", expected_behavior="verify")],
                ),
            ],
            expected_outcomes=[
                Expectation(
                    check_type="keyword_present",
                    check_value="memory",
                    description=f"Placeholder expectation for {name}",
                )
            ],
        )
    )

assert len(ALL_SCENARIOS) == 25
