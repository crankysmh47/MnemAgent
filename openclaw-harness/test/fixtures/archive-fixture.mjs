export const GRAPH_FIXTURE = {
  beliefs: [
    {
      id: 1,
      user_id: "demo-brain",
      category: "preference",
      entity_source: "interface",
      relation: "prefers",
      entity_target: "quiet motion",
      base_utility_q: 0.91,
      injection_count: 7,
      influence_count: 4,
      node_weight: 0.94,
      conviction_score: 0.96,
      created_at: "2026-07-10T08:00:00Z",
      last_accessed: "2026-07-10T08:10:00Z"
    },
    {
      id: 2,
      user_id: "demo-brain",
      category: "preference",
      entity_source: "workspace",
      relation: "prefers",
      entity_target: "focused contrast",
      base_utility_q: 0.86,
      injection_count: 5,
      influence_count: 3,
      node_weight: 0.88,
      conviction_score: 0.9,
      created_at: "2026-07-10T08:01:00Z",
      last_accessed: "2026-07-10T08:11:00Z"
    },
    {
      id: 3,
      user_id: "demo-brain",
      category: "persona",
      entity_source: "operator",
      relation: "works_as",
      entity_target: "design engineer",
      base_utility_q: 0.79,
      injection_count: 4,
      influence_count: 2,
      node_weight: 0.76,
      conviction_score: 0.82,
      created_at: "2026-07-10T08:02:00Z",
      last_accessed: "2026-07-10T08:12:00Z"
    },
    {
      id: 4,
      user_id: "demo-brain",
      category: "persona",
      entity_source: "operator",
      relation: "collaborates_with",
      entity_target: "interface",
      base_utility_q: 0.71,
      injection_count: 2,
      influence_count: 1,
      node_weight: 0.68,
      conviction_score: 0.74,
      created_at: "2026-07-10T08:03:00Z",
      last_accessed: "2026-07-10T08:13:00Z"
    },
    {
      id: 5,
      user_id: "demo-brain",
      category: "system_state",
      entity_source: "archive",
      relation: "uses",
      entity_target: "quiet motion",
      base_utility_q: 0.52,
      injection_count: 1,
      influence_count: 0,
      node_weight: 0.48,
      conviction_score: 0.58,
      created_at: "2026-07-10T08:04:00Z",
      last_accessed: "2026-07-10T08:14:00Z"
    },
    {
      id: 6,
      user_id: "demo-brain",
      category: "system_state",
      entity_source: "design engineer",
      relation: "maintains",
      entity_target: "archive",
      base_utility_q: 0.38,
      injection_count: 0,
      influence_count: 0,
      node_weight: 0.31,
      conviction_score: 0.42,
      created_at: "2026-07-10T08:05:00Z",
      last_accessed: "2026-07-10T08:15:00Z"
    }
  ],
  edges: [
    { source: 1, target: 2, kind: "cluster", weight: 0.65 },
    { source: 1, target: 5, kind: "concept", weight: 0.5 },
    { source: 3, target: 4, kind: "cluster", weight: 0.52 },
    { source: 3, target: 6, kind: "concept", weight: 0.5 },
    { source: 4, target: 1, kind: "bridge", weight: 0.48 }
  ],
  total_turns: 12
};

export const METRICS_FIXTURE = {
  total_beliefs: 6,
  total_sessions: 3,
  avg_q_i: 0.695,
  total_turns: 12,
  ucb_timeline: {
    turns: [8, 9, 10, 11, 12],
    series: {
      interface: [1.11, 1.1, 1.09, 1.08, 1.07],
      workspace: [1.16, 1.14, 1.12, 1.1, 1.09]
    }
  }
};

export const EVENTS_FIXTURE = {
  events: [
    {
      id: 101,
      event_type: "new_belief",
      entity_source: "interface",
      entity_target: "quiet motion",
      detail: { category: "preference" },
      timestamp: "2026-07-10T08:00:00Z"
    },
    {
      id: 102,
      event_type: "injected",
      entity_source: "workspace",
      entity_target: "focused contrast",
      detail: { count: 5 },
      timestamp: "2026-07-10T08:01:00Z"
    },
    {
      id: 103,
      event_type: "influenced",
      entity_source: "operator",
      entity_target: "design engineer",
      detail: { influence_count: 2 },
      timestamp: "2026-07-10T08:02:00Z"
    },
    {
      id: 104,
      event_type: "contradiction",
      entity_source: "operator",
      entity_target: "interface",
      detail: { resolution: "retained" },
      timestamp: "2026-07-10T08:03:00Z"
    },
    {
      id: 105,
      event_type: "decayed",
      entity_source: "archive",
      entity_target: "quiet motion",
      detail: { node_weight: 0.48 },
      timestamp: "2026-07-10T08:04:00Z"
    },
    {
      id: 106,
      event_type: "pruned",
      entity_source: "design engineer",
      entity_target: "archive",
      detail: { node_weight: 0.31 },
      timestamp: "2026-07-10T08:05:00Z"
    }
  ]
};

export const EMPTY_FIXTURE = {
  beliefs: [],
  edges: [],
  total_turns: 0
};
