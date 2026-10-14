# Project-OpenAN

OPEN AN Energy Saving Function - Monorepo for OpenAN platform development.

## Structure

```
Project-OpenAN/
├── upstream/
│   ├── orchestration-center/    # Workflow orchestration, PSOP engine, agents
│   ├── registry-center/         # Agent registry, AgentCards, semantic query
│   └── a2a-t-sdk-python/        # A2A-T SDK for agent communication

```

## Upstream Repositories

Each component is imported from project-openan as a git subtree:

| Directory | Upstream | LLD Role |
|-----------|----------|----------|
| upstream/a2a-t-sdk-python | project-openan/a2a-t-sdk-python | Task-T, Negotiation-T, Authorization-T |
| upstream/registry-center | project-openan/registry-center | AgentCards, semantic query, approval |
| upstream/orchestration-center | project-openan/orchestration-center | PSOP engine, sandbox, SSE, Handler Registry |

## Quick Start

Requires Python 3.12+ and Node.js 20+.

```

## New Work (Energy Saving)

This repository contains additional work beyond the upstream baseline:

- **MAE Agent** - A2A-T negotiation agent for constraint validation
- **Energy Saving Frontend** - React UI with SSE streaming and progress visualization
- **Energy Saving Backend** - Intent management, workflow execution, PSOP templates

### Key Files for Energy Saving

```
upstream/orchestration-center/
├── samples/agents/mae_agent.py           # MAE Agent for negotiation
├── orchestrate/energy_saving/             # Energy Saving module
├── workflow-designer/src/components/energy_saving/  # Frontend component
└── data/workflow_storage/psop/ran_energy_saving_with_mae.json  # PSOP template
```

## Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL (for registry-center)



