"""Shared tech lexicon and entity-dictionary qualification rules."""

from __future__ import annotations

import re

CORE_TECH_DICTIONARY = {
    "python", "javascript", "typescript", "java", "react", "vue", "angular",
    "express", "fastify", "docker", "kubernetes", "postgres", "postgresql",
    "redis", "mysql", "mariadb", "mongodb", "tailwind", "graphql", "rest",
    "aws", "azure", "gcp", "nginx", "linux", "node", "nodejs", "fastapi",
    "django", "flask", "spring", "kotlin", "swift", "rust", "go", "golang",
    "csharp", "dotnet", "terraform", "ansible", "jenkins", "github", "gitlab",
    "vscode", "vim", "webpack", "vite", "nextjs", "nuxt", "svelte", "lodash",
    "gruvbox", "neovim", "emacs",
    "heroku", "ecs", "lambda", "sqlite", "qwen", "openclaw", "prisma", "zod",
}

# Generic graph slots — too broad for keyword extraction.
GENERIC_ENTITY_SLOTS = {
    "user", "affiliation", "preference", "persona", "memory", "context",
    "subject", "team", "client", "company", "name", "role", "task", "goal",
    "status", "update", "detail", "fact", "item", "type", "category",
    "relation", "value", "entity", "system", "state", "prompt", "response",
    "session", "message", "query", "answer", "info", "data", "thing", "stuff",
}

_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def normalize_entity_dict_term(raw: object) -> str | None:
    """Return a single-token dictionary term or None if it should not be indexed."""
    clean = str(raw).strip().lower()
    if len(clean) < 2 or len(clean) > 32:
        return None
    if " " in clean:
        return None
    if not _TOKEN_RE.match(clean):
        return None
    if clean in GENERIC_ENTITY_SLOTS:
        return None
    if clean in CORE_TECH_DICTIONARY:
        return clean
    if clean.isdigit():
        return clean
    if len(clean) >= 3:
        return clean
    return None


def terms_for_entity_dict(entity: object, value: object) -> list[str]:
    """Build deduplicated entity-dictionary terms from a stored belief."""
    terms: list[str] = []
    seen: set[str] = set()
    for raw in (entity, value):
        term = normalize_entity_dict_term(raw)
        if term and term not in seen:
            seen.add(term)
            terms.append(term)
    return terms
