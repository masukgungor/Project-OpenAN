# Project-OpenAN

OPEN AN Energy Saving Function - Monorepo for OpenAN platform development.

## Structure

```
Project-OpenAN/
├── upstream/
│   ├── orchestration-center/    # Workflow orchestration, PSOP engine, agents
│   ├── registry-center/         # Agent registry, AgentCards, semantic query
│   └── a2a-t-sdk-python/        # A2A-T SDK for agent communication
├── mocks/                       # Mock services (electricity price API, MAE)
├── scripts/                     # Dev scripts
└── docs/                        # Documentation
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

### All Services + UIs

```powershell
# Start all services with web UIs
python scripts/dev.py up --ui
```

### Run UC1 (Energy Saving) Demo

```powershell
# Run against mocks
python scripts/dev.py demo

# Run through Orchestration Center
python scripts/dev.py demo-orch
```

### Stop Services

```powershell
python scripts/dev.py down
```

## Syncing with Upstream

To update a component from upstream:

```powershell
git subtree pull --prefix=upstream/orchestration-center \
  https://github.com/project-openan/orchestration-center main

git subtree pull --prefix=upstream/registry-center \
  https://github.com/project-openan/registry-center main

git subtree pull --prefix=upstream/a2a-t-sdk-python \
  https://github.com/project-openan/a2a-t-sdk-python main
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
- Redis (optional, for caching)

## Documentation

See `docs/` directory for detailed documentation:
- `docs/dev-environment.md` - Development environment setup
- `docs/requirements.md` - Functional and non-functional requirements
- `docs/development-backlog.md` - Milestones and work items
