"""
Energy Agent Registration Script

This script registers the Energy Agent and its capabilities to the Registry Center.

Usage:
    python -m orchestrate.energy_saving.register_agent --url http://localhost:8080

Prerequisites:
    - Registry Center must be running
    - Energy Agent must be running
"""

import argparse
import logging
import requests
import json
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ENERGY_AGENT_CARD = {
    "name": "energy-agent",
    "version": "1.0.0",
    "description": "Energy-Saving Agent for OpenAN platform - handles energy saving intent management, electricity price fetching, site classification, cluster optimization, and MAE negotiation",
    "capabilities": [
        {
            "name": "create_intent",
            "description": "Create energy saving intent from user parameters",
            "input_schema": {
                "type": "object",
                "properties": {
                    "region": {"type": "string", "enum": ["north", "south", "east", "west", "central"]},
                    "energy_target": {"type": "string", "enum": ["maximized_saving", "balanced", "experience_first"]},
                    "safeguard": {
                        "type": "object",
                        "properties": {
                            "min_throughput_mbps": {"type": "number"},
                            "max_latency_ms": {"type": "number"},
                            "coverage_maintain": {"type": "boolean"},
                        },
                    },
                    "cluster_id": {"type": "string"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["region", "energy_target"],
            },
        },
        {
            "name": "get_intent",
            "description": "Get energy saving intent by ID",
        },
        {
            "name": "get_electricity_price",
            "description": "Fetch current electricity prices for region",
        },
        {
            "name": "classify_site",
            "description": "Classify site into power band",
        },
        {
            "name": "classify_cluster",
            "description": "Classify all sites in cluster",
        },
        {
            "name": "optimize_cluster",
            "description": "Generate cluster optimization plan",
        },
        {
            "name": "negotiate_with_mae",
            "description": "Negotiate with MAE via A2A-T",
        },
    ],
    "skills": [
        {"id": "energy-saving", "name": "Energy Saving", "description": "Energy saving optimization workflow"},
        {"id": "electricity-price", "name": "Electricity Price", "description": "Electricity price lookup and caching"},
        {"id": "band-classification", "name": "Band Classification", "description": "Site power band classification"},
        {"id": "cluster-optimization", "name": "Cluster Optimization", "description": "Cluster-level electricity cost optimization"},
        {"id": "mae-negotiation", "name": "MAE Negotiation", "description": "A2A-T negotiation with MAE platform"},
    ],
    "endpoint": "http://localhost:5001/api/v1/energy-saving",
    "authentication": {"type": "none"},
    "tags": ["energy-saving", "optimization", "electricity-price", "cluster", "mae"],
}


def register_agent(registry_url: str) -> bool:
    """Register Energy Agent to Registry Center."""
    try:
        # Check if registry is available
        response = requests.get(f"{registry_url}/health", timeout=5)
        if response.status_code != 200:
            logger.error(f"Registry Center not available at {registry_url}")
            return False
        
        # Register agent
        response = requests.post(
            f"{registry_url}/api/v1/agents",
            json=ENERGY_AGENT_CARD,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"Energy Agent registered successfully")
            logger.info(f"Agent ID: {response.json().get('id', 'unknown')}")
            return True
        else:
            logger.error(f"Failed to register agent: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Registry Center: {e}")
        return False


def add_tags(registry_url: str, agent_name: str) -> bool:
    """Add tags to registered agent."""
    try:
        response = requests.put(
            f"{registry_url}/api/v1/agents/{agent_name}/tags",
            json={"tags": ENERGY_AGENT_CARD["tags"]},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        
        if response.status_code == 200:
            logger.info(f"Tags added successfully to {agent_name}")
            return True
        else:
            logger.warning(f"Failed to add tags: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to add tags: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Register Energy Agent to Registry Center")
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Registry Center URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--skip-tags",
        action="store_true",
        help="Skip adding tags to agent",
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Energy Agent registration...")
    logger.info(f"Registry URL: {args.url}")
    logger.info(f"Agent name: {ENERGY_AGENT_CARD['name']}")
    
    success = register_agent(args.url)
    
    if success and not args.skip_tags:
        add_tags(args.url, ENERGY_AGENT_CARD["name"])
    
    if success:
        logger.info("Registration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Registration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
