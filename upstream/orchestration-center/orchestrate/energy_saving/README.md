# Energy Saving Module

## Overview

This module implements the **UC-1: Electricity Price Collaboration for Energy Saving** functionality for the OpenAN platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         orchestration-center                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EnergySavingOrchestrator                         │   │
│  │  (PSOP Workflow: 8 steps)                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Energy Agent                                │   │
│  │  - Intent Management                                                │   │
│  │  - Electricity Price Service                                        │   │
│  │  - Band Classification Service                                      │   │
│  │  - Cluster Optimization Service                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      REST API Layer                                 │   │
│  │  /api/v1/energy-saving/*                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (A2A-T)
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MAE Platform                                       │
│  (External - executes power reduction, tilt adjustment, handover)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
orchestrate/energy_saving/
├── __init__.py
├── agents/
│   ├── __init__.py
│   └── energy_agent.py          # Energy Agent implementation
├── api/
│   ├── __init__.py
│   └── energy_saving_api.py     # REST API endpoints
├── models/
│   ├── __init__.py
│   ├── energy_intent.py         # Intent models
│   ├── electricity_price.py     # Price/band models
│   ├── time_strategy.py         # Time-period strategy models
│   ├── site_classification.py   # Site classification models
│   └── cluster_plan.py          # Optimization plan models
├── services/
│   ├── __init__.py
│   ├── electricity_price_service.py   # Price fetching service
│   ├── band_classification_service.py # Band classification service
│   └── cluster_optimization_service.py # Cluster optimization service
├── workflows/
│   ├── __init__.py
│   └── energy_saving_workflow.py      # PSOP workflow definition
├── register_agent.py            # Agent registration script
└── README.md                    # This file
```

## Quick Start

### 1. Run Tests

```bash
cd D:\OpenAN\orchestration-center
$env:PYTHONPATH = "D:\OpenAN\orchestration-center;$env:PYTHONPATH"
python -m pytest tests/unit/energy_saving/ -v
```

### 2. Start Backend

```bash
cd D:\OpenAN\orchestration-center
python -m orchestrate.start
```

### 3. Register Energy Agent

```bash
cd D:\OpenAN\orchestration-center
python -m orchestrate.energy_saving.register_agent --url http://localhost:8080
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/energy-saving/intent` | POST | Create energy saving intent |
| `/api/v1/energy-saving/intent/{id}` | GET | Get intent by ID |
| `/api/v1/energy-saving/intents` | GET | List all intents |
| `/api/v1/energy-saving/electricity-price/{region}` | GET | Get electricity price |
| `/api/v1/energy-saving/classify-site` | POST | Classify single site |
| `/api/v1/energy-saving/classify-cluster` | POST | Classify cluster sites |
| `/api/v1/energy-saving/optimize-cluster` | POST | Generate optimization plan |
| `/api/v1/energy-saving/negotiate` | POST | Negotiate with MAE |
| `/api/v1/energy-saving/health` | GET | Health check |

## Usage Examples

### Create Energy Saving Intent

```bash
curl -X POST http://localhost:5001/api/v1/energy-saving/intent \
  -H "Content-Type: application/json" \
  -d '{
    "region": "north",
    "energy_target": "maximized_saving",
    "safeguard": {
      "min_throughput_mbps": 10.0,
      "max_latency_ms": 50.0,
      "coverage_maintain": true
    },
    "cluster_id": "CLUSTER001",
    "priority": 5
  }'
```

### Get Electricity Price

```bash
curl http://localhost:5001/api/v1/energy-saving/electricity-price/north
```

### Classify Site

```bash
curl -X POST http://localhost:5001/api/v1/energy-saving/classify-site \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "SITE001",
    "current_power_kw": 2.5
  }'
```

### Classify Cluster

```bash
curl -X POST http://localhost:5001/api/v1/energy-saving/classify-cluster \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_id": "CLUSTER001",
    "sites": [
      {"site_id": "SITE001", "current_power_kw": 2.5},
      {"site_id": "SITE002", "current_power_kw": 1.5},
      {"site_id": "SITE003", "current_power_kw": 3.5}
    ]
  }'
```

## PSOP Workflow Steps

1. **step_1_create_intent** - Create energy saving intent
2. **step_2_get_electricity_price** - Fetch electricity prices
3. **step_3_classify_cluster** - Classify sites into power bands
4. **step_4_optimize_cluster** - Generate optimization plan
5. **step_5_negotiate_with_mae** - Negotiate with MAE via A2A-T
6. **step_6_validate_and_approve** - Validate and approve plan
7. **step_7_execute_plan** - Execute approved plan on MAE
8. **step_8_report_results** - Compile final report

## Power Bands (from PPTX)

| Band | Power Range | Total GHS |
|------|-------------|-----------|
| 1 | 0.00-0.99KW | 8247.66 |
| 2 | 1.00-1.99KW | 10628.25 |
| 3 | 2.00-2.99KW | 11956.25 |
| 4 | 3.00-3.99KW | 15409.75 |
| 5 | 4.00-4.99KW | 17784.09 |

## Time-Period Strategies (from PPTX)

| Time Period | Strategy | Target | Rate Guarantee |
|-------------|----------|--------|----------------|
| 23~5 | Maximized energy saving | - | No |
| 6~9 | Proactive energy saving | 10Mbps | Yes |
| 10~15 | Experience first | No degrade | - |
| 16~17 | Proactive energy saving | 10Mbps | Yes |
| 18~22 | Experience first | No degrade | - |

## Site Classification

- **DOWNGRADE**: Site can have power reduced
- **UPGRADE**: Site needs power increase
- **STABLE_MAINTAINED**: Site should maintain current state

## Tests

```bash
# Run all energy saving tests
python -m pytest tests/unit/energy_saving/ -v

# Run specific test file
python -m pytest tests/unit/energy_saving/test_energy_intent.py -v

# Run integration tests
python -m pytest tests/integration/test_energy_agent.py -v

# Run with coverage
python -m pytest tests/unit/energy_saving/ --cov=orchestrate.energy_saving
```

## Configuration

Environment variables:

```bash
ELECTRICITY_PRICE_CACHE_TTL_SECONDS=300  # 5 minutes cache
ELECTRICITY_PRICE_API_URL=https://api.electricity-provider.com
```

## License

Copyright Huawei 2026
