"""Benchmark scenario definitions for MnemAgent evaluation — 25 scenarios, 5 categories.

All 25 scenarios are fully fleshed out with multi-session conversations and
specific expected outcomes that test hackathon-relevant metrics.
"""

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
    description: str = "",
) -> Scenario:
    """Build a Scenario from compact tuples."""
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
        description=description or name,
        category=category,
        conversations=conversations,
        expected_outcomes=expectations,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Category 1: RECALL (5 scenarios) — cross-session preference memory
# ══════════════════════════════════════════════════════════════════════════════

ALL_SCENARIOS: list[Scenario] = [
    _scenario(
        "pref_recall_1",
        "Simple Preference",
        "recall",
        [
            ("s1", [
                ("I always prefer Python over JavaScript for backend work.", "store python preference"),
            ]),
            ("s2", [
                ("What language should we use for the API?", "recall python from memory"),
            ]),
        ],
        [("keyword_present", "Python", "Should mention Python from stored memory")],
        "User states a clear preference; agent should recall it in a new session.",
    ),
    _scenario(
        "pref_recall_2",
        "Nested Preference",
        "recall",
        [
            ("s1", [
                ("I like minimal code comments. Only explain complex logic.", "store comment preference"),
            ]),
            ("s2", [
                ("Review this function for me.", "minimal comments respecting preference"),
            ]),
        ],
        [("keyword_present", "comment", "Should reference the comment preference")],
        "User prefers minimal comments; review should respect that.",
    ),
    _scenario(
        "pref_recall_3",
        "Tool Preference",
        "recall",
        [
            ("s1", [
                ("I use VS Code with Vim keybindings and the Gruvbox theme.", "store editor prefs"),
            ]),
            ("s2", [
                ("Help me set up my editor for this project.", "recall vs code vim gruvbox"),
            ]),
        ],
        [
            ("keyword_present", "VS Code", "Should mention VS Code"),
            ("keyword_present", "Vim", "Should mention Vim keybindings"),
        ],
        "User specifies editor preferences; new session should recall them.",
    ),
    _scenario(
        "pref_recall_4",
        "Architectural Preference",
        "recall",
        [
            ("s1", [
                ("We always use microservices architecture at our company.", "store microservices preference"),
            ]),
            ("s2", [
                ("Design the system for our new feature.", "design with microservices"),
            ]),
        ],
        [("keyword_present", "microservice", "Should design with microservices")],
        "User states architectural preference; design should follow it.",
    ),
    _scenario(
        "pref_recall_5",
        "Multiple Preferences",
        "recall",
        [
            ("s1", [("I prefer TypeScript for all projects.", "store typescript preference")]),
            ("s2", [("We use PostgreSQL as our database.", "store postgres preference")]),
            ("s3", [("We deploy everything on AWS.", "store aws preference")]),
            ("s4", [("Set up a new project for me.", "use all three preferences")]),
        ],
        [
            ("keyword_present", "TypeScript", "Should use TypeScript"),
            ("keyword_present", "PostgreSQL", "Should use PostgreSQL"),
            ("keyword_present", "AWS", "Should use AWS"),
        ],
        "Multiple preferences taught across sessions; all should be recalled.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # Category 2: CONTRADICTION (5 scenarios) — updating facts without retaining stale ones
    # ══════════════════════════════════════════════════════════════════════════

    _scenario(
        "contradiction_1",
        "Framework Switch",
        "contradiction",
        [
            ("s1", [("We use Express.", "store express")]),
            ("s2", [("We switched to Fastify.", "store fastify, contradict express")]),
            ("s3", [("What framework are we using?", "should recall fastify, not express")]),
        ],
        [
            ("keyword_present", "Fastify", "Should use current framework"),
            ("contradiction_resolved", "express|Fastify", "Should prefer current over stale"),
        ],
        "Framework preference changed; agent must update, not retain old fact.",
    ),
    _scenario(
        "contradiction_2",
        "Deadline Change",
        "contradiction",
        [
            ("s1", [("The project deadline is March 15.", "store deadline march 15")]),
            ("s2", [("Deadline moved to April 1.", "update deadline to april 1")]),
            ("s3", [("When is the deadline?", "recall april 1, not march 15")]),
        ],
        [
            ("keyword_present", "April", "Should mention the new deadline"),
            ("contradiction_resolved", "March|April", "Should use current, not old"),
        ],
        "Deadline changed; agent must use the updated date.",
    ),
    _scenario(
        "contradiction_3",
        "Team Size Change",
        "contradiction",
        [
            ("s1", [("Our team has 5 developers.", "store 5 devs")]),
            ("s2", [("We just hired 3 more, so we have 8 now.", "update to 8 devs")]),
            ("s3", [("How many developers are on our team?", "recall 8, not 5")]),
        ],
        [
            ("keyword_absent", "5 developer", "Should not mention old team size"),
            ("keyword_present", "8", "Should mention current team size"),
        ],
        "Team size updated; old count must not leak.",
    ),
    _scenario(
        "contradiction_4",
        "Technology Correction",
        "contradiction",
        [
            ("s1", [("We are using MySQL for the database.", "store mysql")]),
            ("s2", [("Actually, it is MariaDB, not MySQL.", "correct to mariadb")]),
            ("s3", [("What database are we on?", "recall mariadb, not mysql")]),
        ],
        [
            ("keyword_present", "MariaDB", "Should mention correct database"),
            ("contradiction_resolved", "MySQL|MariaDB", "Should use corrected name"),
        ],
        "Technology name corrected; agent must use the accurate name.",
    ),
    _scenario(
        "contradiction_5",
        "Role Change",
        "contradiction",
        [
            ("s1", [("I am the frontend lead.", "store frontend lead role")]),
            ("s2", [("I just moved to the backend team as tech lead.", "update to backend tech lead")]),
            ("s3", [("What is my role?", "recall backend tech lead")]),
        ],
        [
            ("keyword_present", "backend", "Should mention backend role"),
            ("contradiction_resolved", "frontend|backend", "Should use current role"),
        ],
        "User role changed; agent must acknowledge the new role.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # Category 3: INTERFERENCE (5 scenarios) — proactive interference prevention
    # ══════════════════════════════════════════════════════════════════════════

    _scenario(
        "interference_1",
        "Stale Tech Stack",
        "interference",
        [
            ("s1", [("We use React 16 for our frontend.", "store react 16")]),
            ("s2", [("We upgraded to React 18 last month.", "update to react 18")]),
            ("s3", [("Should we use hooks or class components?", "react 18 -> hooks")]),
        ],
        [
            ("keyword_present", "hook", "Should recommend hooks (React 18+)"),
            ("proactive_interference", "class component|hook", "Should not prefer stale class components"),
        ],
        "Old React version must not interfere with current recommendation.",
    ),
    _scenario(
        "interference_2",
        "Outdated Dependency",
        "interference",
        [
            ("s1", [("We depend on lodash for utility functions.", "store lodash dependency")]),
            ("s2", [("We removed lodash and use native JavaScript methods now.", "remove lodash")]),
            ("s3", [("How should I write a debounce function?", "native js, not lodash")]),
        ],
        [
            ("keyword_absent", "lodash", "Should not suggest lodash"),
            ("keyword_present", "debounce", "Should give native debounce solution"),
        ],
        "Old dependency must not be recommended after removal.",
    ),
    _scenario(
        "interference_3",
        "Replaced Service",
        "interference",
        [
            ("s1", [("We use Heroku for hosting our applications.", "store heroku")]),
            ("s2", [("We migrated to AWS ECS last quarter.", "update to ecs")]),
            ("s3", [("How do we deploy the new service?", "ecs instructions, not heroku")]),
        ],
        [
            ("keyword_present", "ECS", "Should mention ECS"),
            ("proactive_interference", "Heroku|ECS", "Should prefer ECS over Heroku"),
        ],
        "Old hosting platform must not leak into deployment advice.",
    ),
    _scenario(
        "interference_4",
        "Changed Convention",
        "interference",
        [
            ("s1", [("We use camelCase for all variable names.", "store camelCase")]),
            ("s2", [("Team voted to switch to snake_case.", "update to snake_case")]),
            ("s3", [("Write a utility function for processing user data.", "use snake_case")]),
        ],
        [
            ("keyword_present", "snake_case", "Should use snake_case"),
            ("proactive_interference", "camelCase|snake_case", "Should prefer current convention"),
        ],
        "Coding convention changed; old style must not leak.",
    ),
    _scenario(
        "interference_5",
        "Retracted Decision",
        "interference",
        [
            ("s1", [("Let us use GraphQL for the API.", "store graphql decision")]),
            ("s2", [("After research, REST is better for our use case.", "retract graphql, adopt rest")]),
            ("s3", [("Design the API endpoints for our service.", "rest endpoints, not graphql")]),
        ],
        [
            ("keyword_present", "REST", "Should design REST API"),
            ("proactive_interference", "GraphQL|REST", "Should prefer REST over GraphQL"),
        ],
        "Retracted architectural decision must not influence later work.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # Category 4: FORGETTING (5 scenarios) — salience precision + temporal decay
    # ══════════════════════════════════════════════════════════════════════════

    _scenario(
        "forgetting_1",
        "Low Conviction Rejection",
        "forgetting",
        [
            ("s1", [("Maybe we should try Vue sometime.", "low conviction — should reject")]),
            ("s2", [("What frontend framework are we using?", "should not mention vue")]),
        ],
        [("keyword_absent", "Vue", "Should NOT assert Vue as a preference")],
        "Low-conviction hedged statement must not enter memory.",
    ),
    _scenario(
        "forgetting_2",
        "Hedged Statement",
        "forgetting",
        [
            ("s1", [("I am thinking maybe TypeScript, perhaps?", "very low conviction — reject")]),
            ("s2", [("What language should we use for the new module?", "should not assert typescript")]),
        ],
        [
            ("keyword_absent", "TypeScript preference", "Should not assert TypeScript as user preference"),
            ("no_question_asked", "", "Should not need to ask what language (should remain neutral)"),
        ],
        "Hedged, uncertain statement must be rejected by salience auction.",
    ),
    _scenario(
        "forgetting_3",
        "Temporal Decay",
        "forgetting",
        [
            ("s1", [("We need to fix bug #234 urgently — it is critical.", "store urgent bug")]),
            ("s2", [("What should I work on today?", "decayed bug should have lower priority")]),
        ],
        [("keyword_present", "work", "Should suggest current priorities, not only the old bug")],
        "Old priorities decay over time; agent should not fixate on stale urgency.",
    ),
    _scenario(
        "forgetting_4",
        "Information Overload",
        "forgetting",
        [
            ("s1", [
                ("Remember: I like Python.", "store python"),
                ("Also I like dark themes.", "store dark theme"),
                ("My favorite color is blue.", "store blue"),
                ("I drink coffee in the morning.", "store coffee"),
                ("The office is on the 3rd floor.", "store office"),
                ("Our CEO is named Sarah.", "store ceo name"),
                ("We use Jira for tracking.", "store jira"),
                ("Standup is at 9am daily.", "store standup time"),
                ("The wifi password is guest123.", "store wifi"),
                ("Pizza Friday is a tradition.", "store pizza friday"),
            ]),
            ("s2", [("Set up my development environment.", "should use high-conviction preferences")]),
        ],
        [
            ("salience_precision", "Python|dark theme", "Should retain high-utility preferences"),
            ("keyword_present", "Python", "Should remember programming preference"),
        ],
        "Many facts taught; only high-utility, high-conviction ones should survive.",
    ),
    _scenario(
        "forgetting_5",
        "Dormant Memory UCB",
        "forgetting",
        [
            ("s1", [("I love dark mode for everything.", "store dark mode preference")]),
            ("s2", [
                ("What is 2+2?", "unrelated"),
                ("What is the capital of France?", "unrelated"),
                ("Explain what a function is.", "unrelated"),
                ("How does HTTP work?", "unrelated"),
            ]),
            ("s3", [("Set up my development environment.", "dark mode should resurface via UCB")]),
        ],
        [("keyword_present", "dark mode", "Dark mode preference should resurface via UCB exploration")],
        "Dormant memory should resurface through UCB exploration bonus after many turns.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # Category 5: CONTEXT (5 scenarios) — associative recall + context efficiency
    # ══════════════════════════════════════════════════════════════════════════

    _scenario(
        "context_1",
        "10-Session Continuity",
        "context",
        [
            ("s1", [("We use Docker for all deployments.", "store docker")]),
            ("s2", [("Our monitoring stack is Prometheus and Grafana.", "store monitoring")]),
            ("s3", [("We use Kubernetes for orchestration.", "store k8s")]),
            ("s4", [("All our services are written in Go.", "store go")]),
            ("s5", [("We use gRPC for service-to-service communication.", "store grpc")]),
            ("s6", [("Our CI/CD pipeline is on GitHub Actions.", "store github actions")]),
            ("s7", [("We store secrets in HashiCorp Vault.", "store vault")]),
            ("s8", [("Logging goes to Elasticsearch via Fluentd.", "store logging")]),
            ("s9", [("We use Terraform for infrastructure as code.", "store terraform")]),
            ("s10", [("Our primary cloud provider is AWS.", "store aws")]),
            ("s11", [("Describe our infrastructure stack.", "should recall multiple facts")]),
        ],
        [
            ("keyword_present", "Docker", "Should recall Docker"),
            ("keyword_present", "Kubernetes", "Should recall Kubernetes"),
            ("keyword_present", "AWS", "Should recall AWS"),
        ],
        "10 sessions each teach one fact; session 11 should recall multiple relevant facts.",
    ),
    _scenario(
        "context_2",
        "Associative Recall RWR",
        "context",
        [
            ("s1", [("John manages the frontend team.", "store john -> frontend")]),
            ("s2", [("The frontend team uses React for all projects.", "store frontend -> react")]),
            ("s3", [("What does John's team use?", "should chain john -> frontend -> react")]),
        ],
        [("keyword_present", "React", "Should associate John with React via RWR")],
        "RWR associative hop should link John → frontend → React.",
    ),
    _scenario(
        "context_3",
        "Personalization Quality",
        "context",
        [
            ("s1", [("I am a senior engineer with 10 years of experience. Please be concise and technical in your responses.", "store senior+concise persona")]),
            ("s2", [("Explain Docker networking.", "should be concise and technical")]),
        ],
        [
            ("conciseness", "150", "Should be concise (under 150 words) for senior engineer"),
            ("keyword_absent", "Docker is a tool that", "Should not give beginner-level intro"),
        ],
        "Agent should personalize response based on stored persona.",
    ),
    _scenario(
        "context_4",
        "Project Context",
        "context",
        [
            ("s1", [("This project is a fintech application for small businesses. We handle financial data so security is critical.", "store fintech context")]),
            ("s2", [("What security considerations should we have?", "fintech-specific security")]),
        ],
        [
            ("keyword_present", "PCI", "Should mention PCI DSS for fintech"),
            ("keyword_present", "financial", "Should reference financial data protection"),
        ],
        "Stored project context should inform domain-specific security advice.",
    ),
    _scenario(
        "context_5",
        "No False Memory Injection",
        "context",
        [
            ("s1", [("Should I use Ruby for this project?", "no false memory of ruby preference")]),
        ],
        [
            ("keyword_absent", "Ruby prefer", "Must not hallucinate Ruby preference"),
            ("no_question_asked", "", "Should answer without asking clarifying questions about Ruby"),
        ],
        "Agent must not hallucinate preferences that were never taught.",
    ),
]

assert len(ALL_SCENARIOS) == 25, f"Expected 25 scenarios, got {len(ALL_SCENARIOS)}"
