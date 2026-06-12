"""Pre-recorded responses for offline benchmark dry-run mode.

All 25 scenarios have detailed fixtures showing clear night-and-day differences
between MnemOS (with memory) and baseline (without memory) responses.
"""

from __future__ import annotations

from eval.scenarios import ALL_SCENARIOS

# ── Per-scenario fixture responses ──────────────────────────────────────────
# Each entry: { "with_memory": [turn1, turn2, ...], "without_memory": [...] }
# The LAST response in each list is scored against expected_outcomes.

FIXTURE_RESPONSES: dict[str, dict[str, list[str]]] = {
    # ── Recall ──────────────────────────────────────────────────────────
    "pref_recall_1": {
        "with_memory": [
            "Got it — I'll remember you prefer Python for backend work.",
            "Based on your preference, Python is the best choice for the API. It has excellent frameworks like FastAPI and Django.",
        ],
        "without_memory": [
            "Noted.",
            "You could use Python or JavaScript depending on your team's expertise. What does your team prefer?",
        ],
    },
    "pref_recall_2": {
        "with_memory": [
            "I'll keep comments minimal as you prefer.",
            "Here's the review with minimal comments — only the complex logic is explained as you prefer.",
        ],
        "without_memory": [
            "Understood.",
            "Here is a detailed line-by-line review with extensive comments explaining every operation.",
        ],
    },
    "pref_recall_3": {
        "with_memory": [
            "Noted — VS Code with Vim keybindings and Gruvbox theme.",
            "Since you use VS Code with Vim keybindings and Gruvbox theme, I recommend installing the Vim extension and setting `gruvbox` as your color theme.",
        ],
        "without_memory": [
            "Okay, I'll note that.",
            "Which editor do you use? VS Code, IntelliJ, or something else? And do you have any theme preferences?",
        ],
    },
    "pref_recall_4": {
        "with_memory": [
            "I'll remember your company uses microservices architecture.",
            "Following your microservices architecture, I'll design independent services with their own databases, communicating via message queues.",
        ],
        "without_memory": [
            "Got it.",
            "Should we use a microservices approach or a monolithic architecture for this feature?",
        ],
    },
    "pref_recall_5": {
        "with_memory": [
            "TypeScript noted.",
            "PostgreSQL noted.",
            "AWS noted.",
            "Setting up your new project with TypeScript on AWS using PostgreSQL as the database. Here's the configuration...",
        ],
        "without_memory": [
            "Noted.",
            "Noted.",
            "Noted.",
            "What language, database, and cloud provider should I use for this project?",
        ],
    },

    # ── Contradiction ─────────────────────────────────────────────────────
    "contradiction_1": {
        "with_memory": [
            "Express — noted.",
            "Fastify noted — I've updated your stack preference from Express to Fastify.",
            "We are using Fastify now for the backend.",
        ],
        "without_memory": [
            "Express is common.",
            "Fastify is also an option.",
            "Express is a common choice — which framework do you currently use?",
        ],
    },
    "contradiction_2": {
        "with_memory": [
            "Deadline March 15 — noted.",
            "Updated: deadline is now April 1.",
            "The deadline is April 1, per the latest update.",
        ],
        "without_memory": [
            "March 15, got it.",
            "April 1, noted.",
            "I don't have a deadline on record. When is it due?",
        ],
    },
    "contradiction_3": {
        "with_memory": [
            "5 developers — noted.",
            "Updated: team size is now 8 after the hires.",
            "You have 8 developers on the team now, after hiring 3 more.",
        ],
        "without_memory": [
            "5 devs, noted.",
            "8 devs, got it.",
            "I don't have your current team size. How many developers are on the team?",
        ],
    },
    "contradiction_4": {
        "with_memory": [
            "MySQL — noted.",
            "Corrected: you are using MariaDB, not MySQL.",
            "You are using MariaDB for the database.",
        ],
        "without_memory": [
            "MySQL, got it.",
            "MariaDB, noted.",
            "I'm not sure which database you use. MySQL? PostgreSQL?",
        ],
    },
    "contradiction_5": {
        "with_memory": [
            "Frontend lead — noted.",
            "Updated: you are now the backend tech lead.",
            "Your current role is backend tech lead.",
        ],
        "without_memory": [
            "Frontend lead, got it.",
            "Backend tech lead, noted.",
            "I don't have your current role on file. What's your position?",
        ],
    },

    # ── Interference ───────────────────────────────────────────────────────
    "interference_1": {
        "with_memory": [
            "React 16 — noted.",
            "Updated to React 18.",
            "Since you are on React 18, you should use hooks for state management. They are the modern standard for new components.",
        ],
        "without_memory": [
            "React 16, got it.",
            "React 18, noted.",
            "You can use either hooks or class components depending on your React version. If you're on React 16, class components are common.",
        ],
    },
    "interference_2": {
        "with_memory": [
            "Lodash dependency — noted.",
            "Updated: lodash removed, using native JS.",
            "Here is a native JavaScript debounce function using modern ES6 features — no external library needed since you removed that dependency.",
        ],
        "without_memory": [
            "Lodash, noted.",
            "Native JS, got it.",
            "You can use lodash's debounce function like `_.debounce(func, wait)` which is the standard approach.",
        ],
    },
    "interference_3": {
        "with_memory": [
            "Heroku — noted.",
            "Updated: migrated to AWS ECS.",
            "To deploy your new service on AWS ECS, create a task definition, configure your container, and set up an ECS service with the desired count.",
        ],
        "without_memory": [
            "Heroku, got it.",
            "AWS ECS, noted.",
            "You can deploy on Heroku with `git push heroku main` or consider other platforms like AWS or Google Cloud.",
        ],
    },
    "interference_4": {
        "with_memory": [
            "camelCase convention — noted.",
            "Updated: team switched to snake_case.",
            "Here is your utility function using snake_case naming as per your team's current convention.",
        ],
        "without_memory": [
            "camelCase, got it.",
            "snake_case, noted.",
            "Here is the utility function — I used camelCase for variable names, which is standard in JavaScript.",
        ],
    },
    "interference_5": {
        "with_memory": [
            "GraphQL — noted.",
            "REST it is — updated from GraphQL.",
            "Here are the REST API endpoints for your service: GET /users, POST /users, GET /users/:id, etc.",
        ],
        "without_memory": [
            "GraphQL, got it.",
            "REST, noted.",
            "GraphQL is a popular choice — here's a schema design with queries and mutations for your API.",
        ],
    },

    # ── Forgetting ─────────────────────────────────────────────────────────
    "forgetting_1": {
        "with_memory": [
            "Vue is noted as a tentative option — I won't store that as a firm preference since it was uncertain.",
            "I don't have a confirmed frontend framework preference stored for you. Which framework are you currently using?",
        ],
        "without_memory": [
            "Vue could work.",
            "Vue is one option among many frontend frameworks like React and Angular.",
        ],
    },
    "forgetting_2": {
        "with_memory": [
            "I understand you're considering TypeScript, but since it was tentative, I'll wait for a firm decision before storing a preference.",
            "You haven't confirmed a language preference yet. JavaScript and Python are both solid options for this module.",
        ],
        "without_memory": [
            "TypeScript could be good.",
            "TypeScript would work well for this module given your apparent interest in it.",
        ],
    },
    "forgetting_3": {
        "with_memory": [
            "Bug #234 urgency noted — I'll track this.",
            "For today, I suggest you work on your current sprint tasks. Bug #234 was flagged earlier but newer priorities may have superseded it.",
        ],
        "without_memory": [
            "Bug #234, noted.",
            "I don't have your current task list. What's on your plate today?",
        ],
    },
    "forgetting_4": {
        "with_memory": [
            "Python noted as your key programming preference.",
            "Dark themes noted as a strong preference.",
            "Blue color preference noted.",
            "Coffee in the morning, noted.",
            "Office on the 3rd floor, noted.",
            "CEO Sarah, noted.",
            "Jira for task tracking, noted.",
            "Standup at 9am daily, noted.",
            "WiFi password guest123, noted.",
            "Pizza Friday tradition, noted.",
            "Setting up your environment with Python and a dark theme as the most definite preferences. Other details (office floor, wifi password, Jira, etc.) are lower priority.",
        ],
        "without_memory": [
            "Python, got it.",
            "Dark theme, noted.",
            "Blue, good to know.",
            "Coffee drinker, understood.",
            "3rd floor office, noted.",
            "CEO Sarah, got it.",
            "Jira for tracking, noted.",
            "9am standup, noted.",
            "WiFi password, noted.",
            "Pizza Friday, got it!",
            "Setting up your dev environment — what language do you want to use? And do you have any theme preferences?",
        ],
    },
    "forgetting_5": {
        "with_memory": [
            "Dark mode preference noted for everything.",
            "Understood.", "Paris.", "A function is a reusable block of code.", "HTTP is the Hypertext Transfer Protocol.",
            "Setting up your dev environment — including dark mode, which you mentioned you prefer for everything.",
        ],
        "without_memory": [
            "Dark mode, got it.",
            "It's 4.", "The capital is Paris.", "A function is a reusable piece of code.", "HTTP transfers hypertext over the web.",
            "Setting up your development environment. Do you have any preferences for theme or layout?",
        ],
    },

    # ── Context ────────────────────────────────────────────────────────────
    "context_1": {
        "with_memory": [
            "Docker noted.", "Prometheus + Grafana noted.", "Kubernetes noted.", "Go noted.",
            "gRPC noted.", "GitHub Actions noted.", "Vault noted.", "Fluentd + Elasticsearch noted.",
            "Terraform noted.", "AWS noted.",
            "Your infrastructure stack: Docker containers orchestrated by Kubernetes on AWS, with Go services communicating via gRPC, monitored by Prometheus/Grafana, logs to Elasticsearch via Fluentd, secrets in Vault, CI/CD on GitHub Actions, and infrastructure managed by Terraform.",
        ],
        "without_memory": [
            "Noted.", "Noted.", "Noted.", "Noted.",
            "Noted.", "Noted.", "Noted.", "Noted.",
            "Noted.", "Noted.",
            "I don't have your infrastructure details saved. Could you describe your current stack?",
        ],
    },
    "context_2": {
        "with_memory": [
            "John manages the frontend team — noted.",
            "Frontend team uses React — noted.",
            "John's team uses React, since he manages the frontend team and they use React for all projects.",
        ],
        "without_memory": [
            "Noted about John.",
            "React for frontend, got it.",
            "I know John manages a team, but I'm not sure which technology they use. Would you like to specify?",
        ],
    },
    "context_3": {
        "with_memory": [
            "Understood — I'll be concise and technical in all responses for you as a senior engineer.",
            "Docker networking: bridge (default, NAT-based isolation), overlay (multi-host swarm), host (no isolation), macvlan (L2 adjacency). Custom bridges enable DNS resolution. Overlay uses VXLAN with encrypted control plane via IPSec if enabled. Network policies via `iptables` rules. Key commands: `docker network create --driver bridge`, `docker network inspect`.",
        ],
        "without_memory": [
            "Got it, I'll keep responses concise and technical.",
            "Docker is a tool that lets you run applications in containers. Docker networking allows containers to communicate with each other. There are several types of Docker networks: bridge networks (the default), host networks, overlay networks, and macvlan networks. Bridge networks are isolated...",
        ],
    },
    "context_4": {
        "with_memory": [
            "Fintect application, small business focus, financial data handling — security-critical context noted.",
            "For your fintech application handling financial data, key security considerations: PCI DSS compliance for payment card data, encryption at rest and in transit, strict access controls with audit logging, regular penetration testing, and financial regulatory compliance specific to your jurisdiction.",
        ],
        "without_memory": [
            "Noted.",
            "For security, you should consider authentication, authorization, encryption, and regular security audits. These are important for any application.",
        ],
    },
    "context_5": {
        "with_memory": [
            "Ruby could work for this project, but I don't have any stored preference for Ruby in your memory. Your confirmed preferences indicate Python for backend work.",
        ],
        "without_memory": [
            "Ruby is a solid choice! Ruby on Rails is great for web applications. Which language are you considering — Ruby, Python, or something else?",
        ],
    },
}

# ── Per-scenario memory dumps (for memory state checks) ─────────────────────
# Only scenarios that check memory_state or salience_precision need entries.

FIXTURE_MEMORY_DUMPS: dict[str, str] = {
    "pref_recall_1": "backend_language → prefers → python",
    "pref_recall_2": "code_style → prefers → minimal-comments",
    "pref_recall_3": "editor → prefers → VS Code\neditor_keybindings → prefers → Vim\neditor_theme → prefers → Gruvbox",
    "pref_recall_4": "architecture → prefers → microservices",
    "pref_recall_5": "language → prefers → TypeScript\n    database → prefers → PostgreSQL\n    cloud_provider → prefers → AWS",
    "contradiction_1": "backend_framework → prefers → fastify",
    "contradiction_2": "deadline → is → April 1",
    "contradiction_3": "team_size → is → 8",
    "contradiction_4": "database → is → MariaDB",
    "contradiction_5": "user_role → is → backend_tech_lead",
    "interference_1": "frontend_framework → uses → react_18",
    "interference_2": "utils_library → uses → native_js",
    "interference_3": "hosting → uses → aws_ecs",
    "interference_4": "naming_convention → uses → snake_case",
    "interference_5": "api_style → uses → REST",
    "forgetting_1": "",
    "forgetting_2": "",
    "forgetting_3": "bug_234 → status → urgent (decayed)",
    "forgetting_4": "language → prefers → Python\n    theme → prefers → dark",
    "forgetting_5": "theme → prefers → dark_mode",
    "context_1": "deployment → uses → Docker\n    orchestration → uses → Kubernetes\n    cloud → uses → AWS",
    "context_2": "team_manager → John → frontend\n    frontend_tech → uses → React",
    "context_3": "user_role → is → senior_engineer\n    response_style → prefers → concise_technical",
    "context_4": "project_type → is → fintech\n    target_users → is → small_businesses\n    data_type → is → financial",
    "context_5": "",
}

# Ensure all 25 scenarios have fixtures (fill gaps from base set)
for scenario in ALL_SCENARIOS:
    if scenario.id not in FIXTURE_RESPONSES:
        FIXTURE_RESPONSES[scenario.id] = {
            "with_memory": [
                f"[MnemOS] Setup acknowledged with memory context for {scenario.name}.",
                f"[MnemOS] Memory-informed response for {scenario.name}.",
            ],
            "without_memory": [
                f"[Baseline] Setup acknowledged for {scenario.name}.",
                f"[Baseline] Generic response without memory context for {scenario.name}.",
            ],
        }
