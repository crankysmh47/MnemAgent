"""Eval v2 — unguessable arbitrary facts that demand persistent memory.

Key design change: probe questions test recall of information the LLM
CANNOT infer from context. Facts are arbitrary (codenames, version numbers,
personal details) — the only way to answer correctly is through memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eval.scenarios import Expectation


def _e(check: str, value: str, desc: str) -> Expectation:
    return Expectation(check_type=check, check_value=value, description=desc)


@dataclass
class MemorySeed:
    entity: str
    relation: str
    value: str
    category: str = "preference"
    conviction: float = 1.0


@dataclass
class AgenticStep:
    step_index: int
    session_id: str
    phase: str
    user_message: str
    expectations: list[Expectation] = field(default_factory=list)
    label: str = ""
    memory_seed: MemorySeed | None = None


@dataclass
class AgenticScenario:
    id: str
    name: str
    description: str
    category: str
    steps: list[AgenticStep] = field(default_factory=list)

    @property
    def probe_steps(self) -> list[AgenticStep]:
        return [s for s in self.steps if s.phase in ("probe", "contradict") and s.expectations]


AGENTIC_SCENARIOS_V2: list[AgenticScenario] = [
    # ── Scenario 1: Unguessable personal facts ──────────────────────────
    AgenticScenario(
        id="personal_context",
        name="Personal Context Persistence",
        description="Arbitrary personal details taught across sessions — unguessable from probe questions.",
        category="recall",
        steps=[
            AgenticStep(1, "s-a", "teach",
                "I graduated from FAST University in 2023 with a CS degree. My student ID was CS-7841.",
                memory_seed=MemorySeed("graduation_year", "is", "2023", "persona"),
            ),
            AgenticStep(2, "s-a", "teach",
                "My favorite code theme is called 'moonlight-amber' — I use it everywhere.",
                memory_seed=MemorySeed("code_theme", "prefers", "moonlight-amber", "preference"),
            ),
            AgenticStep(3, "s-b", "probe",
                "I'm setting up a new laptop. What theme do I use and what was my student ID?",
                [
                    _e("keyword_present", "moonlight-amber", "Recalls unguessable theme name"),
                    _e("keyword_present", "CS-7841", "Recalls unguessable student ID"),
                ],
                "probe-personal",
            ),
            AgenticStep(4, "s-c", "teach",
                "Actually I switched my theme to 'solarized-dusk' — I found it easier on my eyes.",
                memory_seed=MemorySeed("code_theme", "prefers", "solarized-dusk", "preference", 1.0),
            ),
            AgenticStep(5, "s-d", "probe",
                "What theme am I using now? And when did I graduate?",
                [
                    _e("keyword_present", "solarized-dusk", "Recalls UPDATED theme (contradiction handled)"),
                    _e("keyword_absent", "moonlight-amber", "Old theme must not leak (proactive interference)"),
                    _e("keyword_present", "2023", "Recalls graduation year"),
                ],
                "probe-contradiction",
            ),
        ],
    ),

    # ── Scenario 2: Project context with arbitrary codenames ────────────
    AgenticScenario(
        id="project_codename",
        name="Project Codenames & Versioning",
        description="Arbitrary project names and version numbers — zero contextual cues.",
        category="recall",
        steps=[
            AgenticStep(1, "s-x", "teach",
                "Our main product is codenamed 'Project NightHawk' and the current release is v3.7.2-beta.",
                memory_seed=MemorySeed("project_codename", "is", "Project NightHawk", "system_state"),
            ),
            AgenticStep(2, "s-x", "teach",
                "The database schema version is v12.4 and we use a sharding strategy called 'hex-grid'.",
                memory_seed=MemorySeed("db_schema_version", "is", "v12.4", "system_state"),
            ),
            AgenticStep(3, "s-y", "probe",
                "A new team member needs to know: what's our product codename and current release version?",
                [
                    _e("keyword_present", "NightHawk", "Recalls unguessable product codename"),
                    _e("keyword_present", "3.7.2", "Recalls specific version number"),
                ],
                "probe-codename",
            ),
            AgenticStep(4, "s-z", "probe",
                "The ops team is asking about our sharding strategy and schema version for capacity planning.",
                [
                    _e("keyword_present", "hex-grid", "Recalls unguessable strategy name"),
                    _e("keyword_present", "v12.4", "Recalls schema version"),
                ],
                "probe-sharding",
            ),
        ],
    ),

    # ── Scenario 3: Salience — garbage rejection proof ──────────────────
    AgenticScenario(
        id="salience_proof",
        name="Salience Auction: Garbage Rejection",
        description="Low-conviction hedged statements must NOT enter memory. Confirmed facts must.",
        category="forgetting",
        steps=[
            AgenticStep(1, "s-1", "teach",
                "We definitely use the 'prometheus-prime' monitoring stack for production.",
                memory_seed=MemorySeed("monitoring_stack", "uses", "prometheus-prime", "system_state", 1.0),
            ),
            AgenticStep(2, "s-1", "teach",
                "Maybe we could try that new 'falcon-eye' tool someday. I'm not sure.",
                # NO memory_seed — low conviction, salience should reject
            ),
            AgenticStep(3, "s-1", "teach",
                "Hmm, perhaps 'sky-watch' might be worth looking into. Just a thought.",
                # NO memory_seed — very low conviction
            ),
            AgenticStep(4, "s-2", "probe",
                "What monitoring stack do we use in production? And have we decided on any other monitoring tools?",
                [
                    _e("keyword_present", "prometheus-prime", "Recalls confirmed monitoring stack"),
                    _e("keyword_absent", "falcon-eye", "Hedged tool must NOT be stored"),
                    _e("keyword_absent", "sky-watch", "Speculative tool must NOT be stored"),
                ],
                "probe-salience",
            ),
        ],
    ),

    # ── Scenario 4: Multi-session continuity ────────────────────────────
    AgenticScenario(
        id="cross_session_continuity",
        name="Cross-Session Project Continuity",
        description="Facts spread across 5 sessions — must aggregate all for final probe.",
        category="context",
        steps=[
            AgenticStep(1, "mon", "teach",
                "For our fintech app, the compliance framework is 'regul8-v2' and we report to 'FinCEN' quarterly.",
                memory_seed=MemorySeed("compliance_framework", "uses", "regul8-v2", "system_state"),
            ),
            AgenticStep(2, "tue", "teach",
                "The payment processor is 'Stripe Connect' with idempotency key prefix 'idem-pxy-7'.",
                memory_seed=MemorySeed("payment_processor", "uses", "Stripe Connect", "system_state"),
            ),
            AgenticStep(3, "wed", "teach",
                "Our caching layer uses Redis with a custom eviction policy called 'lru-timed'.",
                memory_seed=MemorySeed("cache_eviction", "uses", "lru-timed", "system_state"),
            ),
            AgenticStep(4, "thu", "teach",
                "The auth system uses JWT with a rotating secret named 'auth-cyclone'.",
                memory_seed=MemorySeed("auth_mechanism", "uses", "auth-cyclone", "system_state"),
            ),
            AgenticStep(5, "fri", "teach",
                "Error tracking is handled by a custom service called 'errant-shepherd'.",
                memory_seed=MemorySeed("error_tracker", "uses", "errant-shepherd", "system_state"),
            ),
            AgenticStep(6, "mon2", "probe",
                "A new engineer needs the full picture. What's our compliance framework, payment processor, auth mechanism, and error tracker?",
                [
                    _e("keyword_present", "regul8-v2", "Recalls compliance framework from Monday"),
                    _e("keyword_present", "Stripe Connect", "Recalls payment processor from Tuesday"),
                    _e("keyword_present", "auth-cyclone", "Recalls auth mechanism from Thursday"),
                    _e("keyword_present", "errant-shepherd", "Recalls error tracker from Friday"),
                ],
                "probe-continuity",
            ),
        ],
    ),
]
