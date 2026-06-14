"""MnemBench scenario definitions — 10 long-running memory evaluation scenarios.

Each scenario is a multi-step workflow that exercises a specific dimension of
memory system quality. Scenarios include teach, probe, and contradict phases
with deterministic expectations for automated scoring.

Scenarios:
  1. ten_session_recall       — 10 sessions, 1 fact each; session 11 probes all 10
  2. contradiction_chain      — 3 sequential contradictions (A→B→C→D)
  3. salience_gate            — 5 hedged + 5 definitive statements; precision gate
  4. interference_gauntlet    — 5 facts taught, then all 5 updated; old values must not leak
  5. dormant_resurrection     — 1 fact, then 15 unrelated turns, then probe
  6. overload_resistance      — 30 rapid-fire facts; high-conviction facts survive
  7. multi_hop_association    — Chain A→B, B→C, C→D; probe asks about A→D
  8. temporal_decay           — Staggered timestamps; oldest facts decay
  9. context_window_efficiency — Token count of injected context stays O(1)
  10. cross_user_isolation    — User A and B facts isolated
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemorySeed:
    """Deterministic fact to store before probing (isolates retrieval from LLM tagging)."""

    entity: str
    relation: str
    value: str
    category: str = "preference"
    conviction: float = 1.0


@dataclass
class MnemBenchStep:
    """One step in a MnemBench scenario.

    Attributes:
        step_index: 1-based index within the scenario.
        session_id: Logical session grouping.
        phase: One of "teach", "probe", "contradict", "distract", "measure".
        user_message: The message sent to the agent.
        expectations: List of Expectation tuples for scoring.
        label: Optional human-readable label.
        memory_seed: Optional seed to pre-store via API.
        metadata: Extra data (e.g., timestamps, token counts).
    """

    step_index: int
    session_id: str
    phase: str  # teach | probe | contradict | distract | measure
    user_message: str
    expectations: list[tuple[str, str, str]] = field(default_factory=list)
    label: str = ""
    memory_seed: MemorySeed | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class MnemBenchScenario:
    """Complete benchmark scenario definition."""

    id: str
    name: str
    description: str
    category: str
    steps: list[MnemBenchStep] = field(default_factory=list)

    @property
    def probe_steps(self) -> list[MnemBenchStep]:
        return [s for s in self.steps if s.phase in ("probe", "contradict") and s.expectations]

    @property
    def teach_steps(self) -> list[MnemBenchStep]:
        return [s for s in self.steps if s.phase == "teach"]

    @property
    def distract_steps(self) -> list[MnemBenchStep]:
        return [s for s in self.steps if s.phase == "distract"]


def _exp(check: str, value: str, desc: str) -> tuple[str, str, str]:
    return (check, value, desc)


def _seed(entity: str, relation: str, value: str, category: str = "preference", conviction: float = 1.0) -> MemorySeed:
    return MemorySeed(entity=entity, relation=relation, value=value, category=category, conviction=conviction)


# ==============================================================================
# Scenario 1: Ten-Session Recall
# ==============================================================================
# 10 sessions, each teaches 1 fact. Session 11 probes all 10 facts.
# Tests cross-session recall at scale — can the memory system retrieve
# 10 independently stored facts into a single coherent response?

TEN_SESSION_RECALL = MnemBenchScenario(
    id="ten_session_recall",
    name="Ten-Session Recall",
    description="10 sessions teach 1 fact each; session 11 probes all 10. Tests cross-session recall at scale.",
    category="recall",
    steps=[
        MnemBenchStep(1, "s1", "teach", "We use Docker for all deployments.",
                       memory_seed=_seed("deployment", "uses", "Docker")),
        MnemBenchStep(2, "s2", "teach", "Our monitoring stack is Prometheus and Grafana.",
                       memory_seed=_seed("monitoring", "uses", "Prometheus and Grafana")),
        MnemBenchStep(3, "s3", "teach", "We use Kubernetes for orchestration.",
                       memory_seed=_seed("orchestration", "uses", "Kubernetes")),
        MnemBenchStep(4, "s4", "teach", "All our services are written in Go.",
                       memory_seed=_seed("language", "uses", "Go")),
        MnemBenchStep(5, "s5", "teach", "We use gRPC for service-to-service communication.",
                       memory_seed=_seed("communication", "uses", "gRPC")),
        MnemBenchStep(6, "s6", "teach", "Our CI/CD pipeline is on GitHub Actions.",
                       memory_seed=_seed("cicd", "uses", "GitHub Actions")),
        MnemBenchStep(7, "s7", "teach", "We store secrets in HashiCorp Vault.",
                       memory_seed=_seed("secrets", "uses", "Vault")),
        MnemBenchStep(8, "s8", "teach", "Logging goes to Elasticsearch via Fluentd.",
                       memory_seed=_seed("logging", "uses", "Elasticsearch and Fluentd")),
        MnemBenchStep(9, "s9", "teach", "We use Terraform for infrastructure as code.",
                       memory_seed=_seed("iac", "uses", "Terraform")),
        MnemBenchStep(10, "s10", "teach", "Our primary cloud provider is AWS.",
                       memory_seed=_seed("cloud", "uses", "AWS")),
        MnemBenchStep(11, "s11", "probe",
                       "Describe our full infrastructure stack for a new team member.",
                       [
                           _exp("keyword_present", "Docker", "Recalls Docker"),
                           _exp("keyword_present", "Kubernetes", "Recalls Kubernetes"),
                           _exp("keyword_present", "Go", "Recalls Go"),
                           _exp("keyword_present", "gRPC", "Recalls gRPC"),
                           _exp("keyword_present", "Prometheus", "Recalls monitoring"),
                           _exp("keyword_present", "GitHub Actions", "Recalls CI/CD"),
                           _exp("keyword_present", "Vault", "Recalls secrets"),
                           _exp("keyword_present", "Elasticsearch", "Recalls logging"),
                           _exp("keyword_present", "Terraform", "Recalls IaC"),
                           _exp("keyword_present", "AWS", "Recalls cloud provider"),
                       ],
                       label="probe-all-10",
                       metadata={"expected_facts": 10}),
    ],
)


# ==============================================================================
# Scenario 2: Contradiction Chain
# ==============================================================================
# 3 contradictions in sequence: A→B, then B→C, then C→D.
# Tests whether the memory system can perform multi-hop contradiction
# resolution (updating through multiple intermediate states).

CONTRADICTION_CHAIN = MnemBenchScenario(
    id="contradiction_chain",
    name="Contradiction Chain",
    description="3 sequential contradictions (A->B->C->D). Tests multi-hop contradiction resolution.",
    category="contradiction",
    steps=[
        MnemBenchStep(1, "s1", "teach", "We use Express for our API.",
                       memory_seed=_seed("backend_framework", "uses", "Express")),
        MnemBenchStep(2, "s1", "probe",
                       "What framework do we use for APIs?",
                       [_exp("keyword_present", "Express", "Recalls initial framework")],
                       "probe-initial"),
        MnemBenchStep(3, "s2", "contradict", "We have migrated from Express to Fastify as our API framework.",
                       memory_seed=_seed("backend_framework", "uses", "Fastify")),
        MnemBenchStep(4, "s2", "probe",
                       "What API framework should I use for new routes?",
                       [
                           _exp("keyword_present", "Fastify", "Uses Fastify after first migration"),
                           _exp("contradiction_resolved", "Express|Fastify", "Does not prefer stale Express"),
                       ],
                       label="probe-after-first-migration"),
        MnemBenchStep(5, "s3", "contradict", "The team decided to standardize on Koa instead of Fastify.",
                       memory_seed=_seed("backend_framework", "uses", "Koa")),
        MnemBenchStep(6, "s3", "probe",
                       "What framework is our API running on now?",
                       [
                           _exp("keyword_present", "Koa", "Uses Koa after second migration"),
                           _exp("keyword_absent", "Express", "Does not mention Express"),
                           _exp("contradiction_resolved", "Fastify|Koa", "Does not prefer intermediate Fastify"),
                       ],
                       label="probe-after-second-migration"),
        MnemBenchStep(7, "s4", "contradict", "After evaluation, we are going with Hono for all new API development.",
                       memory_seed=_seed("backend_framework", "uses", "Hono")),
        MnemBenchStep(8, "s4", "probe",
                       "Quick check — what is our current API framework?",
                       [
                           _exp("keyword_present", "Hono", "Uses Hono after third migration"),
                           _exp("keyword_absent", "Express", "Stale Express suppressed"),
                           _exp("keyword_absent", "Fastify", "Intermediate Fastify suppressed"),
                           _exp("contradiction_resolved", "Koa|Hono", "Does not prefer intermediate Koa"),
                       ],
                       label="probe-after-third-migration"),
    ],
)


# ==============================================================================
# Scenario 3: Salience Gate
# ==============================================================================
# 5 hedged statements ("maybe X") interleaved with 5 definitive statements.
# Tests precision of what gets stored vs rejected — high-conviction facts must
# be retained, tentative statements must be gated out.

SALIENCE_GATE = MnemBenchScenario(
    id="salience_gate",
    name="Salience Gate",
    description="5 hedged + 5 definitive statements. Tests precision of memory gating.",
    category="salience",
    steps=[
        # Hedged (should be rejected)
        MnemBenchStep(1, "s1", "teach", "Maybe we could try Vue for the dashboard someday."),
        MnemBenchStep(2, "s1", "teach", "I might consider using Tailwind, but I'm not sure yet."),
        MnemBenchStep(3, "s1", "teach", "Perhaps we should migrate to GraphQL eventually."),
        MnemBenchStep(4, "s1", "teach", "I was thinking maybe we could use MongoDB, but no decision yet."),
        MnemBenchStep(5, "s1", "teach", "Possibly we could try serverless, but it's just an idea."),
        # Definitive (should be stored)
        MnemBenchStep(6, "s2", "teach", "We always use TypeScript for all frontend code.",
                       memory_seed=_seed("frontend_language", "uses", "TypeScript")),
        MnemBenchStep(7, "s2", "teach", "Our API returns JSON responses exclusively.",
                       memory_seed=_seed("api_format", "uses", "JSON")),
        MnemBenchStep(8, "s2", "teach", "All code must pass ESLint before merging.",
                       memory_seed=_seed("code_quality", "requires", "ESLint")),
        MnemBenchStep(9, "s2", "teach", "We deploy only through our CI/CD pipeline.",
                       memory_seed=_seed("deployment", "requires", "CI/CD pipeline")),
        MnemBenchStep(10, "s2", "teach", "All services require unit tests with at least 80%% coverage.",
                       memory_seed=_seed("testing", "requires", "80% coverage")),
        # Probes
        MnemBenchStep(11, "s3", "probe",
                       "What language should I use for this frontend component?",
                       [
                           _exp("keyword_present", "TypeScript", "Definitive TypeScript stored"),
                           _exp("keyword_absent", "Vue", "Hedged Vue rejected"),
                       ],
                       label="probe-frontend-lang"),
        MnemBenchStep(12, "s3", "probe",
                       "What are our API and testing standards?",
                       [
                           _exp("keyword_present", "JSON", "JSON format stored"),
                           _exp("keyword_present", "80%", "Coverage requirement stored"),
                           _exp("keyword_absent", "GraphQL", "Hedged GraphQL rejected"),
                           _exp("keyword_absent", "MongoDB", "Hedged MongoDB rejected"),
                       ],
                       label="probe-standards"),
        MnemBenchStep(13, "s3", "probe",
                       "How should I deploy my new service?",
                       [
                           _exp("keyword_present", "CI/CD", "CI/CD requirement stored"),
                           _exp("keyword_absent", "serverless", "Hedged serverless rejected"),
                       ],
                       label="probe-deployment"),
    ],
)


# ==============================================================================
# Scenario 4: Interference Gauntlet
# ==============================================================================
# 5 facts taught, then all 5 updated. Old values must NOT leak into final probes.
# Tests both proactive and retroactive interference prevention.

INTERFERENCE_GAUNTLET = MnemBenchScenario(
    id="interference_gauntlet",
    name="Interference Gauntlet",
    description="5 facts taught, then all 5 updated. Old values must not leak.",
    category="interference",
    steps=[
        # Teach originals
        MnemBenchStep(1, "s1", "teach", "Our server runs on Ubuntu 20.04.",
                       memory_seed=_seed("os", "version", "Ubuntu 20.04")),
        MnemBenchStep(2, "s1", "teach", "We use Python 3.9 for all services.",
                       memory_seed=_seed("python", "version", "3.9")),
        MnemBenchStep(3, "s1", "teach", "Our database is PostgreSQL 12.",
                       memory_seed=_seed("database", "version", "PostgreSQL 12")),
        MnemBenchStep(4, "s1", "teach", "We deploy on Heroku.",
                       memory_seed=_seed("hosting", "provider", "Heroku")),
        MnemBenchStep(5, "s1", "teach", "We use Flask for our API framework.",
                       memory_seed=_seed("api_framework", "uses", "Flask")),
        # Update all 5
        MnemBenchStep(6, "s2", "contradict", "We upgraded the servers to Ubuntu 22.04.",
                       memory_seed=_seed("os", "version", "Ubuntu 22.04")),
        MnemBenchStep(7, "s2", "contradict", "All projects have migrated to Python 3.12.",
                       memory_seed=_seed("python", "version", "3.12")),
        MnemBenchStep(8, "s2", "contradict", "We migrated our database to PostgreSQL 16.",
                       memory_seed=_seed("database", "version", "PostgreSQL 16")),
        MnemBenchStep(9, "s2", "contradict", "We moved all hosting from Heroku to AWS ECS.",
                       memory_seed=_seed("hosting", "provider", "AWS ECS")),
        MnemBenchStep(10, "s2", "contradict", "We replaced Flask with FastAPI for all new services.",
                       memory_seed=_seed("api_framework", "uses", "FastAPI")),
        # Probes
        MnemBenchStep(11, "s3", "probe",
                       "What OS version are our servers running?",
                       [
                           _exp("keyword_present", "22.04", "New OS version used"),
                           _exp("keyword_absent", "20.04", "Old OS version suppressed"),
                       ],
                       label="probe-os"),
        MnemBenchStep(12, "s3", "probe",
                       "What Python version and database are we using?",
                       [
                           _exp("keyword_present", "3.12", "New Python version"),
                           _exp("keyword_present", "PostgreSQL 16", "New database version"),
                           _exp("keyword_absent", "3.9", "Old Python not mentioned"),
                           _exp("keyword_absent", "PostgreSQL 12", "Old database not mentioned"),
                       ],
                       label="probe-python-db"),
        MnemBenchStep(13, "s3", "probe",
                       "Where do we host our services and what API framework do we use?",
                       [
                           _exp("keyword_present", "ECS", "New hosting platform"),
                           _exp("keyword_present", "FastAPI", "New framework"),
                           _exp("keyword_absent", "Heroku", "Old hosting not mentioned"),
                           _exp("keyword_absent", "Flask", "Old framework not mentioned"),
                       ],
                       label="probe-hosting-framework"),
    ],
)


# ==============================================================================
# Scenario 5: Dormant Resurrection
# ==============================================================================
# Teach a single strong preference, then 15 completely unrelated turns,
# then probe. Tests whether the memory system's exploration bonus (UCB)
# surfaces dormant but relevant facts after long distraction.

DORMANT_RESURRECTION = MnemBenchScenario(
    id="dormant_resurrection",
    name="Dormant Resurrection",
    description="Teach 1 fact, then 15 unrelated turns, then probe. Tests UCB exploration surfacing dormant facts.",
    category="forgetting",
    steps=[
        MnemBenchStep(1, "s1", "teach", "I always prefer dark mode for every interface I use.",
                       memory_seed=_seed("theme", "prefers", "dark_mode")),
        MnemBenchStep(2, "s1", "teach", "Dark mode helps me code for longer hours without eye strain."),
        # 15 distracting turns
        MnemBenchStep(3, "d1", "distract", "What is the capital of France?",
                       metadata={"expected": "Paris"}),
        MnemBenchStep(4, "d1", "distract", "Explain what a TCP handshake is.",
                       metadata={"expected": "SYN, SYN-ACK, ACK"}),
        MnemBenchStep(5, "d1", "distract", "What is 2+2?",
                       metadata={"expected": "4"}),
        MnemBenchStep(6, "d1", "distract", "How does HTTP caching work?",
                       metadata={"expected": "Cache-Control, ETag"}),
        MnemBenchStep(7, "d1", "distract", "What is the square root of 144?",
                       metadata={"expected": "12"}),
        MnemBenchStep(8, "d1", "distract", "Write a hello world in Rust.",
                       metadata={"expected": "fn main"}),
        MnemBenchStep(9, "d1", "distract", "What is the difference between TCP and UDP?",
                       metadata={"expected": "connection-oriented vs connectionless"}),
        MnemBenchStep(10, "d1", "distract", "Define idempotency in HTTP.",
                       metadata={"expected": "same result regardless of repetitions"}),
        MnemBenchStep(11, "d1", "distract", "Explain the CAP theorem.",
                       metadata={"expected": "Consistency, Availability, Partition Tolerance"}),
        MnemBenchStep(12, "d1", "distract", "What is Big O notation?",
                       metadata={"expected": "asymptotic complexity"}),
        MnemBenchStep(13, "d1", "distract", "How does DNS resolution work?",
                       metadata={"expected": "recursive lookup"}),
        MnemBenchStep(14, "d1", "distract", "What is the water cycle?",
                       metadata={"expected": "evaporation, condensation, precipitation"}),
        MnemBenchStep(15, "d1", "distract", "Explain what CI/CD means.",
                       metadata={"expected": "continuous integration, continuous deployment"}),
        MnemBenchStep(16, "d1", "distract", "What is the speed of light?",
                       metadata={"expected": "299,792,458 m/s"}),
        MnemBenchStep(17, "d1", "distract", "Explain MVC architecture.",
                       metadata={"expected": "Model, View, Controller"}),
        # Probe — relevant to UI preferences
        MnemBenchStep(18, "s2", "probe",
                       "Set up my IDE. What theme should I use?",
                       [
                           _exp("keyword_present", "dark", "Dark mode preference resurfaces after distraction"),
                       ],
                       label="probe-dormant-resurrection"),
    ],
)


# ==============================================================================
# Scenario 6: Overload Resistance
# ==============================================================================
# 30 rapid-fire facts in a single session. Tests that the memory graph doesn't
# bloat with low-value facts while high-utility, high-conviction facts survive.
# Probe targets 3 high-conviction facts seeded at high conviction.

OVERLOAD_RESISTANCE = MnemBenchScenario(
    id="overload_resistance",
    name="Overload Resistance",
    description="30 rapid-fire facts in one session. High-conviction facts survive memory pressure.",
    category="salience",
    steps=[
        MnemBenchStep(1, "s1", "teach", "I use Python for all data science work.",
                       memory_seed=_seed("ds_language", "uses", "Python", conviction=0.9)),
        MnemBenchStep(2, "s1", "teach", "The office is on the 3rd floor."),
        MnemBenchStep(3, "s1", "teach", "I like coffee in the morning."),
        MnemBenchStep(4, "s1", "teach", "My favorite color is blue."),
        MnemBenchStep(5, "s1", "teach", "Our CEO is named Sarah."),
        MnemBenchStep(6, "s1", "teach", "We use Jira for task tracking.",
                       memory_seed=_seed("task_tracker", "uses", "Jira", conviction=0.9)),
        MnemBenchStep(7, "s1", "teach", "Standup is at 9am daily."),
        MnemBenchStep(8, "s1", "teach", "The wifi password is guest123."),
        MnemBenchStep(9, "s1", "teach", "Pizza Friday is a tradition."),
        MnemBenchStep(10, "s1", "teach", "I prefer window seats."),
        MnemBenchStep(11, "s1", "teach", "The building has a gym."),
        MnemBenchStep(12, "s1", "teach", "We have unlimited PTO."),
        MnemBenchStep(13, "s1", "teach", "The kitchen has a nespresso machine."),
        MnemBenchStep(14, "s1", "teach", "Our main client is Acme Corp."),
        MnemBenchStep(15, "s1", "teach", "The project started in January 2024."),
        MnemBenchStep(16, "s1", "teach", "We have a team of 12 engineers."),
        MnemBenchStep(17, "s1", "teach", "Quarterly reviews are in March."),
        MnemBenchStep(18, "s1", "teach", "We use Slack for internal communication."),
        MnemBenchStep(19, "s1", "teach", "The fire drill is on the first Friday."),
        MnemBenchStep(20, "s1", "teach", "Our code repository is on GitHub."),
        MnemBenchStep(21, "s1", "teach", "We follow agile with two-week sprints.",
                       memory_seed=_seed("methodology", "uses", "agile", conviction=0.9)),
        MnemBenchStep(22, "s1", "teach", "The break room has a foosball table."),
        MnemBenchStep(23, "s1", "teach", "We have a company offsite in Q2."),
        MnemBenchStep(24, "s1", "teach", "I use a standing desk."),
        MnemBenchStep(25, "s1", "teach", "Our design tool is Figma."),
        MnemBenchStep(26, "s1", "teach", "We use Notion for documentation."),
        MnemBenchStep(27, "s1", "teach", "The CTO's name is Mark."),
        MnemBenchStep(28, "s1", "teach", "We have monthly team lunches."),
        MnemBenchStep(29, "s1", "teach", "Our uptime SLA is 99.9%."),
        MnemBenchStep(30, "s1", "teach", "We do blameless postmortems."),
        # Probe for high-conviction facts
        MnemBenchStep(31, "s2", "probe",
                       "Set up my data science environment and tell me how we track work.",
                       [
                           _exp("keyword_present", "Python", "High-conviction Python remembered"),
                           _exp("keyword_present", "Jira", "High-conviction Jira remembered"),
                           _exp("keyword_present", "agile", "High-conviction agile remembered"),
                       ],
                       label="probe-overload-survival"),
    ],
)


# ==============================================================================
# Scenario 7: Multi-Hop Association (RWR)
# ==============================================================================
# Teach chain: A→B, B→C, C→D. Probe asks about A→D.
# Tests whether the memory system can perform associative hops using
# Random Walk with Restart (RWR) or equivalent graph traversal.

MULTI_HOP_ASSOCIATION = MnemBenchScenario(
    id="multi_hop_association",
    name="Multi-Hop Association",
    description="Chain A->B->C->D. Probe asks about A->D. Tests RWR associative hops.",
    category="context",
    steps=[
        MnemBenchStep(1, "s1", "teach", "Alice is the lead of the frontend team.",
                       memory_seed=_seed("person", "leads", "frontend_team", category="persona")),
        MnemBenchStep(2, "s1", "teach", "The frontend team uses React for all projects.",
                       memory_seed=_seed("frontend_team", "uses", "React", category="system_state")),
        MnemBenchStep(3, "s2", "teach", "React components are styled with Tailwind CSS.",
                       memory_seed=_seed("React", "uses", "Tailwind CSS", category="system_state")),
        MnemBenchStep(4, "s2", "teach", "Tailwind CSS is configured with a custom design system.",
                       memory_seed=_seed("Tailwind", "configured_with", "custom_design_system", category="system_state")),
        # Traverse: Alice → frontend_team → React → Tailwind → custom_design_system
        MnemBenchStep(5, "s3", "probe",
                       "What design system does Alice's team use for their components?",
                       [
                           _exp("keyword_present", "Tailwind", "Associates Alice -> frontend -> React -> Tailwind"),
                           _exp("keyword_present", "custom design", "Reaches final hop: Alice -> ... -> design system"),
                       ],
                       label="probe-3-hop"),
        # Also probe the direct association
        MnemBenchStep(6, "s3", "probe",
                       "What framework does the frontend team use?",
                       [
                           _exp("keyword_present", "React", "Direct association frontend_team -> React"),
                       ],
                       label="probe-direct-hop"),
    ],
)


# ==============================================================================
# Scenario 8: Temporal Decay
# ==============================================================================
# Teach facts with staggered timestamps. Oldest facts should have lowest
# confidence / be forgotten, while recent ones should be remembered.

TEMPORAL_DECAY = MnemBenchScenario(
    id="temporal_decay",
    name="Temporal Decay",
    description="Teach facts with staggered timestamps. Oldest facts should decay.",
    category="forgetting",
    steps=[
        MnemBenchStep(1, "s1", "teach",
                       "The project was initially called Project Phoenix (old name).",
                       metadata={"simulated_timestamp": "2024-01-15T10:00:00Z",
                                 "decay_priority": "low"},
                       memory_seed=_seed("project_codename_old", "was", "Phoenix")),
        MnemBenchStep(2, "s1", "teach",
                       "The original tech lead was Mike (he left the company).",
                       metadata={"simulated_timestamp": "2024-01-20T10:00:00Z",
                                 "decay_priority": "low"},
                       memory_seed=_seed("tech_lead_old", "was", "Mike")),
        MnemBenchStep(3, "s1", "teach",
                       "We were using CircleCI for CI/CD (migrated away).",
                       metadata={"simulated_timestamp": "2024-02-01T10:00:00Z",
                                 "decay_priority": "low"},
                       memory_seed=_seed("cicd_old", "was", "CircleCI")),
        # More recent facts — higher priority
        MnemBenchStep(4, "s1", "teach",
                       "The project was renamed to Project Aether last quarter.",
                       metadata={"simulated_timestamp": "2024-06-01T10:00:00Z",
                                 "decay_priority": "high"},
                       memory_seed=_seed("project_codename", "is", "Aether")),
        MnemBenchStep(5, "s1", "teach",
                       "The current tech lead is Priya.",
                       metadata={"simulated_timestamp": "2024-06-10T10:00:00Z",
                                 "decay_priority": "high"},
                       memory_seed=_seed("tech_lead", "is", "Priya")),
        MnemBenchStep(6, "s1", "teach",
                       "We now use GitHub Actions for CI/CD.",
                       metadata={"simulated_timestamp": "2024-06-15T10:00:00Z",
                                 "decay_priority": "high"},
                       memory_seed=_seed("cicd", "uses", "GitHub Actions")),
        # Very recent fact
        MnemBenchStep(7, "s1", "teach",
                       "The project deadline has been set to December 15, 2024.",
                       metadata={"simulated_timestamp": "2024-07-01T10:00:00Z",
                                 "decay_priority": "highest"},
                       memory_seed=_seed("deadline", "is", "December 15")),
        # Probes
        MnemBenchStep(8, "s2", "probe",
                       "What is the current project name and who is the tech lead?",
                       [
                           _exp("keyword_present", "Aether", "Recent project name remembered"),
                           _exp("keyword_present", "Priya", "Recent tech lead remembered"),
                           _exp("keyword_absent", "Phoenix", "Old project name decayed"),
                           _exp("keyword_absent", "Mike", "Old tech lead decayed"),
                       ],
                       label="probe-current"),
        MnemBenchStep(9, "s2", "probe",
                       "What CI/CD do we use and what is the deadline?",
                       [
                           _exp("keyword_present", "GitHub Actions", "Recent CI/CD remembered"),
                           _exp("keyword_present", "December", "Recent deadline remembered"),
                           _exp("keyword_absent", "CircleCI", "Old CI/CD decayed"),
                       ],
                       label="probe-cicd-deadline"),
    ],
)


# ==============================================================================
# Scenario 9: Context Window Efficiency
# ==============================================================================
# Measure token count of injected memory context as the graph grows.
# A good memory system keeps injected context O(1) (only relevant facts)
# rather than O(n) (dumping all facts). This scenario teaches 50 facts
# then measures the /api/memory/context size.

CONTEXT_WINDOW_EFFICIENCY = MnemBenchScenario(
    id="context_window_efficiency",
    name="Context Window Efficiency",
    description="Measure token count of injected memory context. Should stay O(1) as graph grows.",
    category="context",
    steps=[
        # Teach 50 low-value facts to grow the graph
        MnemBenchStep(1, "s1", "teach",
                       "Fact number 1: the sky is blue."),
        MnemBenchStep(2, "s1", "teach",
                       "Fact number 2: water is wet."),
        MnemBenchStep(3, "s1", "teach",
                       "Fact number 3: fire is hot."),
        MnemBenchStep(4, "s1", "teach",
                       "Fact number 4: grass is green."),
        MnemBenchStep(5, "s1", "teach",
                       "Fact number 5: snow is cold."),
        MnemBenchStep(6, "s1", "teach",
                       "Fact number 6: the sun is bright."),
        MnemBenchStep(7, "s1", "teach",
                       "Fact number 7: the moon orbits Earth."),
        MnemBenchStep(8, "s1", "teach",
                       "Fact number 8: fish live in water."),
        MnemBenchStep(9, "s1", "teach",
                       "Fact number 9: birds can fly."),
        MnemBenchStep(10, "s1", "teach",
                       "Fact number 10: trees produce oxygen."),
        MnemBenchStep(11, "s1", "teach",
                       "Fact number 11: diamonds are hard."),
        MnemBenchStep(12, "s1", "teach",
                       "Fact number 12: gold is malleable."),
        MnemBenchStep(13, "s1", "teach",
                       "Fact number 13: copper conducts electricity."),
        MnemBenchStep(14, "s1", "teach",
                       "Fact number 14: helium is lighter than air."),
        MnemBenchStep(15, "s1", "teach",
                       "Fact number 15: salt dissolves in water."),
        MnemBenchStep(16, "s1", "teach",
                       "Fact number 16: the Earth rotates."),
        MnemBenchStep(17, "s1", "teach",
                       "Fact number 17: gravity pulls things down."),
        MnemBenchStep(18, "s1", "teach",
                       "Fact number 18: light travels in straight lines."),
        MnemBenchStep(19, "s1", "teach",
                       "Fact number 19: sound needs a medium."),
        MnemBenchStep(20, "s1", "teach",
                       "Fact number 20: magnets attract iron."),
        MnemBenchStep(21, "s1", "teach",
                       "Fact number 21: ice floats on water."),
        MnemBenchStep(22, "s1", "teach",
                       "Fact number 22: steam is water vapor."),
        MnemBenchStep(23, "s1", "teach",
                       "Fact number 23: clouds are made of water droplets."),
        MnemBenchStep(24, "s1", "teach",
                       "Fact number 24: the sky appears blue due to Rayleigh scattering."),
        MnemBenchStep(25, "s1", "teach",
                       "Fact number 25: photosynthesis converts CO2 to oxygen."),
        MnemBenchStep(26, "s1", "teach",
                       "Fact number 26: the heart pumps blood."),
        MnemBenchStep(27, "s1", "teach",
                       "Fact number 27: the brain controls the body."),
        MnemBenchStep(28, "s1", "teach",
                       "Fact number 28: DNA carries genetic information."),
        MnemBenchStep(29, "s1", "teach",
                       "Fact number 29: cells are the basic unit of life."),
        MnemBenchStep(30, "s1", "teach",
                       "Fact number 30: evolution is change over time."),
        MnemBenchStep(31, "s1", "teach",
                       "Fact number 31: atoms are mostly empty space."),
        MnemBenchStep(32, "s1", "teach",
                       "Fact number 32: electrons are negatively charged."),
        MnemBenchStep(33, "s1", "teach",
                       "Fact number 33: protons are positively charged."),
        MnemBenchStep(34, "s1", "teach",
                       "Fact number 34: neutrons have no charge."),
        MnemBenchStep(35, "s1", "teach",
                       "Fact number 35: water is H2O."),
        MnemBenchStep(36, "s1", "teach",
                       "Fact number 36: carbon dioxide is CO2."),
        MnemBenchStep(37, "s1", "teach",
                       "Fact number 37: methane is CH4."),
        MnemBenchStep(38, "s1", "teach",
                       "Fact number 38: oxygen is O2."),
        MnemBenchStep(39, "s1", "teach",
                       "Fact number 39: nitrogen is N2."),
        MnemBenchStep(40, "s1", "teach",
                       "Fact number 40: hydrogen is H2."),
        MnemBenchStep(41, "s1", "teach",
                       "Fact number 41: the Python keyword is 'def'."),
        MnemBenchStep(42, "s1", "teach",
                       "Fact number 42: the 'return' keyword exits a function."),
        MnemBenchStep(43, "s1", "teach",
                       "Fact number 43: a 'class' defines an object template."),
        MnemBenchStep(44, "s1", "teach",
                       "Fact number 44: 'import' loads a module."),
        MnemBenchStep(45, "s1", "teach",
                       "Fact number 45: 'try' starts error handling."),
        MnemBenchStep(46, "s1", "teach",
                       "Fact number 46: 'except' catches errors."),
        MnemBenchStep(47, "s1", "teach",
                       "Fact number 47: 'finally' runs cleanup."),
        MnemBenchStep(48, "s1", "teach",
                       "Fact number 48: 'with' manages resources."),
        MnemBenchStep(49, "s1", "teach",
                       "Fact number 49: 'yield' creates generators."),
        MnemBenchStep(50, "s1", "teach",
                       "Fact number 50: 'async' defines coroutines."),
        # Probe with a relevant question — should only inject relevant context
        MnemBenchStep(51, "s2", "probe",
                       "What Python keywords should I use to define a function?",
                       [
                           _exp("keyword_present", "def", "Relevant fact found through memory"),
                       ],
                       label="probe-efficient-context",
                       metadata={"total_facts_taught": 50, "expected_injected_facts": "<5"}),
        # Measure: request a context dump to analyze token count
        MnemBenchStep(52, "s2", "measure",
                       "/api/memory/context",
                       metadata={"measure_type": "context_size"},
                       label="measure-context-size"),
    ],
)


# ==============================================================================
# Scenario 10: Cross-User Isolation
# ==============================================================================
# Teach facts for User A and User B. Verify User A's probe doesn't leak
# User B's facts. Tests user-level memory isolation.

CROSS_USER_ISOLATION = MnemBenchScenario(
    id="cross_user_isolation",
    name="Cross-User Isolation",
    description="User A and B taught separate facts. Verify no cross-user leakage.",
    category="context",
    steps=[
        # User A sessions
        MnemBenchStep(1, "user_a_s1", "teach",
                       "My name is Alice and I work on the frontend team.",
                       memory_seed=_seed("user_identity", "is", "Alice", category="persona")),
        MnemBenchStep(2, "user_a_s1", "teach",
                       "I prefer morning standups at 8am.",
                       memory_seed=_seed("standup_time", "prefers", "8am")),
        MnemBenchStep(3, "user_a_s1", "teach",
                       "My favorite stack is React with Tailwind CSS.",
                       memory_seed=_seed("stack", "prefers", "React and Tailwind")),
        MnemBenchStep(4, "user_a_s1", "teach",
                       "I have a cat named Whiskers.",
                       memory_seed=_seed("pet", "has", "cat named Whiskers", category="persona")),
        # User B sessions (interleaved)
        MnemBenchStep(5, "user_b_s1", "teach",
                       "My name is Bob and I work on the backend team.",
                       memory_seed=_seed("user_identity", "is", "Bob", category="persona")),
        MnemBenchStep(6, "user_b_s1", "teach",
                       "I prefer late standups at 10am.",
                       memory_seed=_seed("standup_time", "prefers", "10am")),
        MnemBenchStep(7, "user_b_s1", "teach",
                       "My favorite stack is Go with PostgreSQL.",
                       memory_seed=_seed("stack", "prefers", "Go and PostgreSQL")),
        MnemBenchStep(8, "user_b_s1", "teach",
                       "I have a dog named Rover.",
                       memory_seed=_seed("pet", "has", "dog named Rover", category="persona")),
        # User A probe — must NOT leak Bob's facts
        MnemBenchStep(9, "user_a_s2", "probe",
                       "What is my name, what team do I work on, and what is my favorite stack?",
                       [
                           _exp("keyword_present", "Alice", "User A's own name recalled"),
                           _exp("keyword_present", "React", "User A's stack remembered"),
                           _exp("keyword_present", "Tailwind", "User A's styling remembered"),
                           _exp("keyword_absent", "Bob", "User B's name NOT leaked"),
                           _exp("keyword_absent", "Go", "User B's language NOT leaked"),
                           _exp("keyword_absent", "dog", "User B's pet NOT leaked"),
                           _exp("keyword_absent", "Rover", "User B's dog NOT leaked"),
                       ],
                       label="probe-user-a-isolation"),
        # User B probe — must NOT leak Alice's facts
        MnemBenchStep(10, "user_b_s2", "probe",
                       "What is my name, what team do I work on, and what is my favorite stack?",
                       [
                           _exp("keyword_present", "Bob", "User B's own name recalled"),
                           _exp("keyword_present", "Go", "User B's stack remembered"),
                           _exp("keyword_present", "PostgreSQL", "User B's database remembered"),
                           _exp("keyword_absent", "Alice", "User A's name NOT leaked"),
                           _exp("keyword_absent", "Tailwind", "User A's styling NOT leaked"),
                           _exp("keyword_absent", "cat", "User A's pet NOT leaked"),
                           _exp("keyword_absent", "Whiskers", "User A's cat NOT leaked"),
                       ],
                       label="probe-user-b-isolation"),
    ],
)


# ==============================================================================
# Master list of all MnemBench scenarios
# ==============================================================================

ALL_MNEMBENCH_SCENARIOS: list[MnemBenchScenario] = [
    TEN_SESSION_RECALL,
    CONTRADICTION_CHAIN,
    SALIENCE_GATE,
    INTERFERENCE_GAUNTLET,
    DORMANT_RESURRECTION,
    OVERLOAD_RESISTANCE,
    MULTI_HOP_ASSOCIATION,
    TEMPORAL_DECAY,
    CONTEXT_WINDOW_EFFICIENCY,
    CROSS_USER_ISOLATION,
]

assert len(ALL_MNEMBENCH_SCENARIOS) == 10, (
    f"Expected exactly 10 MnemBench scenarios, got {len(ALL_MNEMBENCH_SCENARIOS)}"
)
