"""Fixture responses for agentic benchmark dry-run — advantage grows per probe."""

from __future__ import annotations

from eval.agentic_scenarios import AGENTIC_SCENARIOS, AgenticScenario

# with_memory: high scores that improve on harder probes
# without_memory: flat/generic scores that degrade on compound probes

_WITH_MEMORY: dict[str, dict[int, str]] = {
    "compound_stack": {
        2: "Use Python for the new microservice.",
        4: "Python and PostgreSQL match our stack.",
        7: "FastAPI on AWS is our standard.",
        8: "We use Python, PostgreSQL, FastAPI on AWS for all backend work.",
    },
    "contradiction_arc": {
        2: "We are on Express.",
        4: "Use Fastify for the new route handlers.",
        5: "Our backend framework is Fastify.",
    },
    "salience_noise": {
        4: "Write the component in TypeScript.",
        5: "Style it with Tailwind CSS.",
    },
    "project_continuity": {
        3: "Sarah leads the Phoenix project.",
        6: "Phoenix is due March 15 and uses microservices architecture.",
        8: "Phoenix is led by Sarah, uses microservices, Auth0 for auth, deadline March 15.",
    },
}

_WITHOUT_MEMORY: dict[str, dict[int, str]] = {
    "compound_stack": {
        2: "You could use Python or Node.js depending on your team.",
        4: "Many teams use PostgreSQL or MySQL — what does yours use?",
        7: "FastAPI or Flask on AWS or GCP — which do you prefer?",
        8: "Which stack does your organization prefer? I can suggest options.",
    },
    "contradiction_arc": {
        2: "Express is a popular choice for APIs.",
        4: "Express or Fastify could work — which do you use?",
        5: "Common frameworks include Express and Fastify.",
    },
    "salience_noise": {
        4: "You could use TypeScript or JavaScript. Which do you prefer?",
        5: "What CSS framework does your team use?",
    },
    "project_continuity": {
        3: "Who is the project lead on your team?",
        6: "What is the deadline and architecture for your project?",
        8: "I'd need more context about the project to write a brief.",
    },
}


def get_fixture_response(scenario_id: str, step_index: int, mode: str) -> str:
    """Return canned response for dry-run mode."""
    fixtures = _WITH_MEMORY if mode == "with_memory" else _WITHOUT_MEMORY
    return fixtures.get(scenario_id, {}).get(
        step_index,
        "Acknowledged." if mode == "with_memory" else "Could you provide more details?",
    )


def get_fixture_memory_dump(scenario_id: str, step_index: int) -> str:
    """Return synthetic memory dump for dry-run scoring."""
    dumps = {
        "compound_stack": "python → prefers → backend | postgresql | fastapi | aws",
        "contradiction_arc": "backend_framework → prefers → fastify",
        "salience_noise": "frontend → prefers → typescript | tailwind",
        "project_continuity": "phoenix → lead → sarah | march-15 | microservices | auth0",
    }
    return dumps.get(scenario_id, "")
