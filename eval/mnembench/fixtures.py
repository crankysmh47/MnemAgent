"""Pre-recorded responses and memory dumps for MnemBench dry-run mode.

All 10 scenarios have fixture responses showing clear differences between
a memory-augmented system (with_memory) and a baseline without memory.
"""

from __future__ import annotations

# ── Per-scenario fixture responses ───────────────────────────────────────────
# with_memory: responds correctly using stored facts
# without_memory: generic or asks clarifying questions

FIXTURE_RESPONSES: dict[str, dict[str, dict[int, str]]] = {
    "ten_session_recall": {
        "with_memory": {
            11: (
                "Our infrastructure stack: Docker containers deployed on AWS, "
                "orchestrated by Kubernetes. Services are written in Go and communicate "
                "via gRPC. We use Prometheus and Grafana for monitoring, with logging "
                "to Elasticsearch through Fluentd. Our CI/CD runs on GitHub Actions, "
                "secrets managed by HashiCorp Vault, and infrastructure provisioned "
                "via Terraform."
            ),
        },
        "without_memory": {
            11: (
                "I don't have details about your infrastructure stack saved. Could you "
                "tell me what technologies you use for deployment, orchestration, monitoring, "
                "and CI/CD?"
            ),
        },
    },
    "contradiction_chain": {
        "with_memory": {
            2: "We currently use Express for our API framework.",
            4: "We are now using Fastify after migrating from Express.",
            6: "Our API framework is Koa. We migrated from Fastify.",
            8: "We are now using Hono for all new API development.",
        },
        "without_memory": {
            2: "Express is a common framework for APIs.",
            4: "What framework does your team use? Express or something else?",
            6: "I don't have your current framework recorded. Which one are you using?",
            8: "Common API frameworks include Express, Fastify, Koa, and Hono. Which does your team use?",
        },
    },
    "salience_gate": {
        "with_memory": {
            11: "You should use TypeScript for this frontend component, as per your team standard.",
            12: "Our API returns JSON responses and we require at least 80% test coverage on all services.",
            13: "All deployments go through our CI/CD pipeline. That is our standard process.",
        },
        "without_memory": {
            11: "You could use TypeScript or JavaScript — what does your team prefer?",
            12: "What are your API and testing standards? Do you have specific requirements?",
            13: "How does your team typically deploy services? I can provide instructions.",
        },
    },
    "interference_gauntlet": {
        "with_memory": {
            11: "Our servers run Ubuntu 22.04 after the upgrade.",
            12: "We use Python 3.12 and PostgreSQL 16 across all services.",
            13: "We host on AWS ECS and use FastAPI for our API framework.",
        },
        "without_memory": {
            11: "I'm not sure what OS version your servers are running. Can you tell me?",
            12: "What Python version and database does your team use?",
            13: "Where does your team host services and what framework do you use?",
        },
    },
    "dormant_resurrection": {
        "with_memory": {
            18: "Since you prefer dark mode for all interfaces, I recommend setting your IDE to a dark theme like One Dark Pro or Dracula. This will be easier on your eyes during long coding sessions."
        },
        "without_memory": {
            18: "Do you have a preference for light or dark theme? There are many great options available."
        },
    },
    "overload_resistance": {
        "with_memory": {
            31: "Setting up your data science environment with Python. For task tracking, we use Jira with two-week agile sprints."
        },
        "without_memory": {
            31: "What language do you use for data science? And how does your team track work?"
        },
    },
    "multi_hop_association": {
        "with_memory": {
            5: "Alice's team uses React components styled with Tailwind CSS, configured with a custom design system.",
            6: "The frontend team uses React for all their projects.",
        },
        "without_memory": {
            5: "I don't know what design system Alice's team uses. Could you tell me more about their tech stack?",
            6: "I know there is a frontend team but I don't have their technology choices recorded.",
        },
    },
    "temporal_decay": {
        "with_memory": {
            8: "The current project name is Aether and the tech lead is Priya.",
            9: "We use GitHub Actions for CI/CD and the deadline is December 15, 2024.",
        },
        "without_memory": {
            8: "I don't have your current project details. What is the project name and who leads it?",
            9: "What CI/CD tool does your team use and when is the deadline?",
        },
    },
    "context_window_efficiency": {
        "with_memory": {
            51: "You should use the 'def' keyword to define a function in Python.",
        },
        "without_memory": {
            51: "Python uses 'def' to define functions and 'return' to return values. Is there anything specific you want to know?"
        },
    },
    "cross_user_isolation": {
        "with_memory": {
            9: "Your name is Alice, you work on the frontend team, and your favorite stack is React with Tailwind CSS.",
            10: "Your name is Bob, you work on the backend team, and your favorite stack is Go with PostgreSQL.",
        },
        "without_memory": {
            9: "I don't have your details saved. What is your name, team, and tech stack?",
            10: "I don't have your details saved. What is your name, team, and tech stack?",
        },
    },
}

# ── Per-scenario memory dumps ────────────────────────────────────────────────

FIXTURE_MEMORY_DUMPS: dict[str, str] = {
    "ten_session_recall": (
        "deployment → uses → Docker\n"
        "monitoring → uses → Prometheus and Grafana\n"
        "orchestration → uses → Kubernetes\n"
        "language → uses → Go\n"
        "communication → uses → gRPC\n"
        "cicd → uses → GitHub Actions\n"
        "secrets → uses → Vault\n"
        "logging → uses → Elasticsearch and Fluentd\n"
        "iac → uses → Terraform\n"
        "cloud → uses → AWS"
    ),
    "contradiction_chain": "backend_framework → uses → Hono",
    "salience_gate": (
        "frontend_language → uses → TypeScript\n"
        "api_format → uses → JSON\n"
        "code_quality → requires → ESLint\n"
        "deployment → requires → CI/CD pipeline\n"
        "testing → requires → 80% coverage"
    ),
    "interference_gauntlet": (
        "os → version → Ubuntu 22.04\n"
        "python → version → 3.12\n"
        "database → version → PostgreSQL 16\n"
        "hosting → provider → AWS ECS\n"
        "api_framework → uses → FastAPI"
    ),
    "dormant_resurrection": "theme → prefers → dark_mode",
    "overload_resistance": (
        "ds_language → uses → Python\n"
        "task_tracker → uses → Jira\n"
        "methodology → uses → agile"
    ),
    "multi_hop_association": (
        "person → leads → frontend_team\n"
        "frontend_team → uses → React\n"
        "React → uses → Tailwind CSS\n"
        "Tailwind → configured_with → custom_design_system"
    ),
    "temporal_decay": (
        "project_codename → is → Aether\n"
        "tech_lead → is → Priya\n"
        "cicd → uses → GitHub Actions\n"
        "deadline → is → December 15"
    ),
    "context_window_efficiency": (
        "The sky is blue.\n"
        "Water is wet.\n"
        "[... 48 other facts ...]\n"
        "Python keyword 'def' defines functions."
    ),
    "cross_user_isolation": (
        "[User: alice] user_identity → is → Alice\n"
        "[User: bob] user_identity → is → Bob"
    ),
}

# ── Token count estimates for context window efficiency scoring ──────────────

FIXTURE_TOKEN_COUNTS: dict[str, dict[str, int]] = {
    "context_window_efficiency": {
        "with_memory": 120,    # ~O(1) — only injects relevant context
        "without_memory": 0,   # no memory at all
    },
}

# ── Latency estimates (ms) for latency scoring ───────────────────────────────

FIXTURE_LATENCIES: dict[str, dict[str, dict[int, float]]] = {
    "ten_session_recall": {
        "with_memory": {11: 850.0},
        "without_memory": {11: 320.0},
    },
    "contradiction_chain": {
        "with_memory": {2: 300.0, 4: 350.0, 6: 340.0, 8: 360.0},
        "without_memory": {2: 280.0, 4: 300.0, 6: 290.0, 8: 310.0},
    },
    "salience_gate": {
        "with_memory": {11: 400.0, 12: 420.0, 13: 410.0},
        "without_memory": {11: 310.0, 12: 320.0, 13: 300.0},
    },
    "interference_gauntlet": {
        "with_memory": {11: 380.0, 12: 450.0, 13: 440.0},
        "without_memory": {11: 300.0, 12: 310.0, 13: 290.0},
    },
    "dormant_resurrection": {
        "with_memory": {18: 700.0},
        "without_memory": {18: 280.0},
    },
    "overload_resistance": {
        "with_memory": {31: 500.0},
        "without_memory": {31: 300.0},
    },
    "multi_hop_association": {
        "with_memory": {5: 480.0, 6: 350.0},
        "without_memory": {5: 290.0, 6: 280.0},
    },
    "temporal_decay": {
        "with_memory": {8: 380.0, 9: 390.0},
        "without_memory": {8: 280.0, 9: 300.0},
    },
    "context_window_efficiency": {
        "with_memory": {51: 450.0, 52: 100.0},
        "without_memory": {51: 300.0, 52: 80.0},
    },
    "cross_user_isolation": {
        "with_memory": {9: 420.0, 10: 430.0},
        "without_memory": {9: 300.0, 10: 290.0},
    },
}


def get_fixture_response(scenario_id: str, step_index: int, mode: str) -> str:
    """Return canned response for dry-run mode."""
    scenario_fixtures = FIXTURE_RESPONSES.get(scenario_id, {})
    mode_fixtures = scenario_fixtures.get(mode, {})
    return mode_fixtures.get(
        step_index,
        "Acknowledged." if mode == "with_memory" else "Could you provide more details?",
    )


def get_fixture_memory_dump(scenario_id: str) -> str:
    """Return synthetic memory dump for dry-run scoring."""
    return FIXTURE_MEMORY_DUMPS.get(scenario_id, "")


def get_fixture_latency(scenario_id: str, step_index: int, mode: str) -> float:
    """Return canned latency in ms for dry-run mode."""
    scenario_latencies = FIXTURE_LATENCIES.get(scenario_id, {})
    mode_latencies = scenario_latencies.get(mode, {})
    return mode_latencies.get(step_index, 300.0)


def get_fixture_token_count(scenario_id: str, mode: str) -> int:
    """Return estimated token count for context window efficiency."""
    return FIXTURE_TOKEN_COUNTS.get(scenario_id, {}).get(mode, 0)
