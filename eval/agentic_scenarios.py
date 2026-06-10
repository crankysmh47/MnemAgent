"""Multi-step agentic benchmark scenarios — memory advantage compounds over probes."""

from __future__ import annotations

from dataclasses import dataclass, field

from eval.scenarios import Expectation


@dataclass
class MemorySeed:
    """Deterministic fact to store before probing (isolates retrieval from LLM tagging)."""

    entity: str
    relation: str
    value: str
    category: str = "preference"
    conviction: float = 1.0


@dataclass
class AgenticStep:
    """One step in a multi-turn agentic workflow."""

    step_index: int
    session_id: str
    phase: str  # teach | probe | contradict
    user_message: str
    expectations: list[Expectation] = field(default_factory=list)
    label: str = ""
    memory_seed: MemorySeed | None = None


@dataclass
class AgenticScenario:
    """Scenario where probe difficulty increases as more facts are taught."""

    id: str
    name: str
    description: str
    category: str
    steps: list[AgenticStep] = field(default_factory=list)

    @property
    def probe_steps(self) -> list[AgenticStep]:
        return [s for s in self.steps if s.phase in ("probe", "contradict") and s.expectations]


def _exp(check: str, value: str, desc: str) -> Expectation:
    return Expectation(check_type=check, check_value=value, description=desc)


AGENTIC_SCENARIOS: list[AgenticScenario] = [
    AgenticScenario(
        id="compound_stack",
        name="Compound Stack Recall",
        description="Interleaved teach/probe — each step adds facts; probes need 1→2→3→4",
        category="compound",
        steps=[
            AgenticStep(
                1, "s1", "teach", "We always use Python for all backend services.",
                memory_seed=MemorySeed("backend_language", "prefers", "Python"),
            ),
            AgenticStep(
                2, "s2", "probe",
                "What language should the new microservice use?",
                [_exp("keyword_present", "Python", "Recalls language preference")],
                "probe-1-fact",
            ),
            AgenticStep(
                3, "s3", "teach", "Our standard database is PostgreSQL.",
                memory_seed=MemorySeed("database", "prefers", "PostgreSQL"),
            ),
            AgenticStep(
                4, "s4", "probe",
                "What language and database should the API service use?",
                [
                    _exp("keyword_present", "Python", "Recalls language"),
                    _exp("keyword_present", "PostgreSQL", "Recalls database"),
                ],
                "probe-2-facts",
            ),
            AgenticStep(
                5, "s5", "teach", "We build APIs with FastAPI, not Flask.",
                memory_seed=MemorySeed("api_framework", "prefers", "FastAPI"),
            ),
            AgenticStep(
                6, "s6", "teach", "We deploy everything on AWS.",
                memory_seed=MemorySeed("deployment", "prefers", "AWS"),
            ),
            AgenticStep(
                7, "s7", "probe",
                "Which API framework and cloud platform fit our stack?",
                [
                    _exp("keyword_present", "FastAPI", "Recalls API framework"),
                    _exp("keyword_present", "AWS", "Recalls deployment"),
                ],
                "probe-2-facts-mid",
            ),
            AgenticStep(
                8, "s8", "probe",
                "Summarize our full backend stack for a new engineer.",
                [
                    _exp("keyword_present", "Python", "Stack includes Python"),
                    _exp("keyword_present", "PostgreSQL", "Stack includes PostgreSQL"),
                    _exp("keyword_present", "FastAPI", "Stack includes FastAPI"),
                    _exp("keyword_present", "AWS", "Stack includes AWS"),
                ],
                "probe-4-facts",
            ),
        ],
    ),
    AgenticScenario(
        id="contradiction_arc",
        name="Contradiction Arc",
        description="Framework switch mid-workflow; stale memory must not resurface",
        category="contradiction",
        steps=[
            AgenticStep(
                1, "s1", "teach", "We are definitely using Express for the API.",
                memory_seed=MemorySeed("backend_framework", "prefers", "Express"),
            ),
            AgenticStep(
                2, "s2", "probe",
                "What HTTP framework are we on?",
                [_exp("keyword_present", "Express", "Recalls initial framework")],
                "probe-before-switch",
            ),
            AgenticStep(
                3, "s3", "contradict", "We switched to Fastify. Express is deprecated for us.",
                memory_seed=MemorySeed("backend_framework", "prefers", "Fastify", conviction=1.0),
            ),
            AgenticStep(
                4, "s4", "probe",
                "What framework should I use for the new route handlers?",
                [
                    _exp("keyword_present", "Fastify", "Uses updated framework"),
                    _exp("contradiction_resolved", "express|Fastify", "Does not prefer stale Express"),
                ],
                "probe-after-switch",
            ),
            AgenticStep(
                5, "s5", "probe",
                "Quick check — what's our backend framework?",
                [
                    _exp("keyword_present", "Fastify", "Persistent correction"),
                    _exp("keyword_absent", "Express", "Stale fact suppressed"),
                ],
                "probe-persistence",
            ),
        ],
    ),
    AgenticScenario(
        id="salience_noise",
        name="Salience vs Noise",
        description="Hedged facts rejected; firm facts recalled under probe pressure",
        category="salience",
        steps=[
            AgenticStep(1, "s1", "teach", "Maybe we could try Vue for the dashboard someday."),
            AgenticStep(
                2, "s2", "teach", "We always use TypeScript for all frontend code.",
                memory_seed=MemorySeed("frontend_language", "prefers", "TypeScript"),
            ),
            AgenticStep(
                3, "s3", "teach", "Tailwind CSS is our only approved styling approach.",
                memory_seed=MemorySeed("styling", "prefers", "Tailwind CSS"),
            ),
            AgenticStep(
                4, "s4", "probe",
                "What frontend language should I write this component in?",
                [
                    _exp("keyword_present", "TypeScript", "Recalls firm frontend preference"),
                    _exp("keyword_absent", "Vue", "Does not treat hedged Vue as stored"),
                ],
                "probe-language",
            ),
            AgenticStep(
                5, "s5", "probe",
                "How should I style the new settings page?",
                [
                    _exp("keyword_present", "Tailwind", "Recalls styling preference"),
                    _exp("no_question_asked", "", "Does not ask which CSS framework"),
                ],
                "probe-style",
            ),
        ],
    ),
    AgenticScenario(
        id="project_continuity",
        name="Project Continuity",
        description="Interleaved Phoenix facts; probes compound across sessions",
        category="continuity",
        steps=[
            AgenticStep(
                1, "s1", "teach", "Project codename is Phoenix.",
                memory_seed=MemorySeed("phoenix", "codename", "Phoenix", category="system_state"),
            ),
            AgenticStep(
                2, "s2", "teach", "Phoenix team lead is Sarah.",
                memory_seed=MemorySeed("phoenix", "lead", "Sarah", category="persona"),
            ),
            AgenticStep(
                3, "s3", "probe",
                "Who leads the Phoenix project?",
                [_exp("keyword_present", "Sarah", "Recalls team lead")],
                "probe-single",
            ),
            AgenticStep(
                4, "s4", "teach", "The Phoenix deadline is March 15.",
                memory_seed=MemorySeed("phoenix", "deadline", "March 15", category="system_state"),
            ),
            AgenticStep(
                5, "s5", "teach", "Phoenix uses a microservices architecture.",
                memory_seed=MemorySeed("phoenix", "architecture", "microservices", category="system_state"),
            ),
            AgenticStep(
                6, "s6", "probe",
                "When is Phoenix due and what architecture do we use?",
                [
                    _exp("keyword_present", "March", "Recalls deadline"),
                    _exp("keyword_present", "microservice", "Recalls architecture"),
                ],
                "probe-double",
            ),
            AgenticStep(
                7, "s7", "teach", "Phoenix auth is handled by Auth0.",
                memory_seed=MemorySeed("phoenix", "auth", "Auth0", category="system_state"),
            ),
            AgenticStep(
                8, "s8", "probe",
                "Give me a one-paragraph Phoenix project brief for a new hire.",
                [
                    _exp("keyword_present", "Phoenix", "Names project"),
                    _exp("keyword_present", "Sarah", "Mentions lead"),
                    _exp("keyword_present", "Auth0", "Mentions auth"),
                    _exp("relevance", "March,microservice", "Covers deadline and architecture"),
                ],
                "probe-synthesis",
            ),
        ],
    ),
]
