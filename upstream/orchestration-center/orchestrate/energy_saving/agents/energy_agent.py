import uuid
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from orchestrate.energy_saving.models import (
    EnergySavingIntent,
    EnergySavingIntentCreate,
    EnergySavingIntentResponse,
    ElectricityPriceData,
    ElectricityPriceResponse,
    DEFAULT_PRICE_BANDS,
    DEFAULT_TIME_SLOT_PRICES,
    TimePeriodStrategy,
    get_strategy_for_hour,
    get_time_period_for_hour,
    SiteClassification,
    SiteClass,
    classify_band as classify_band_fn,
    classify_site as classify_site_fn,
    ClusterClassificationResult,
    ClusterOptimizationPlan,
    TrafficMigrationAction,
    NegotiationRequest,
    NegotiationResponse,
)

logger = logging.getLogger(__name__)


class EnergyAgent:
    """Energy Agent for OpenAN Energy-Saving Function.
    
    Responsibilities:
    - Manage energy saving intents
    - Fetch electricity prices
    - Classify sites into power bands
    - Generate cluster optimization plans
    - Negotiate with MAE via A2A-T
    """

    def __init__(self):
        self.name = "energy-agent"
        self.version = "1.0.0"
        self.description = "Energy-Saving Agent for OpenAN platform"
        self._intents: Dict[str, EnergySavingIntent] = {}
        self._price_cache: Dict[str, ElectricityPriceData] = {}
        self._intents_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "energy_intents.json")
        self._load_intents()

    def get_agent_card(self) -> Dict[str, Any]:
        """Return agent card for registry."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": [
                {"name": "create_intent", "description": "Create energy saving intent"},
                {"name": "get_intent", "description": "Get intent by ID"},
                {"name": "get_electricity_price", "description": "Get electricity price for region"},
                {"name": "classify_site", "description": "Classify site into power band"},
                {"name": "classify_cluster", "description": "Classify cluster sites"},
                {"name": "optimize_cluster", "description": "Generate cluster optimization plan"},
                {"name": "negotiate_with_mae", "description": "Negotiate with MAE via A2A-T"},
            ],
            "skills": [
                {"id": "energy-saving", "name": "Energy Saving", "description": "Energy saving optimization"},
                {"id": "electricity-price", "name": "Electricity Price", "description": "Electricity price lookup"},
                {"id": "band-classification", "name": "Band Classification", "description": "Site band classification"},
                {"id": "cluster-optimization", "name": "Cluster Optimization", "description": "Cluster-level optimization"},
            ],
            "endpoint": "http://localhost:5001/api/v1/energy-agent",
        }

    # Intent Management
    def _load_intents(self):
        """Load intents from JSON file."""
        logger.info(f"[_load_intents] Checking file: {self._intents_file}")
        logger.info(f"[_load_intents] File exists: {os.path.exists(self._intents_file)}")
        if os.path.exists(self._intents_file):
            try:
                with open(self._intents_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"[_load_intents] Loaded data: {data}")
                    for intent_id, intent_data in data.items():
                        intent = EnergySavingIntent(**intent_data)
                        self._intents[intent.intent_id] = intent
                    logger.info(f"[_load_intents] Loaded {len(self._intents)} intents from {self._intents_file}")
            except Exception as e:
                logger.warning(f"[_load_intents] Failed to load intents from {self._intents_file}: {e}")
        else:
            logger.warning(f"[_load_intents] File does not exist: {self._intents_file}")

    def _save_intents(self):
        """Save intents to JSON file."""
        try:
            os.makedirs(os.path.dirname(self._intents_file), exist_ok=True)
            data = {k: v.model_dump() for k, v in self._intents.items()}
            with open(self._intents_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(self._intents)} intents to {self._intents_file}")
        except Exception as e:
            logger.warning(f"Failed to save intents to {self._intents_file}: {e}")

    def create_intent(self, intent_create: EnergySavingIntentCreate) -> EnergySavingIntent:
        """Create a new energy saving intent."""
        intent_id = f"INT-{uuid.uuid4().hex[:8].upper()}"
        intent = EnergySavingIntent(
            intent_id=intent_id,
            region=intent_create.region,
            energy_target=intent_create.energy_target,
            safeguard=intent_create.safeguard,
            cluster_id=intent_create.cluster_id,
            priority=intent_create.priority,
            source=intent_create.source,
        )
        self._intents[intent_id] = intent
        self._save_intents()
        logger.info(f"Created energy intent: {intent_id}")
        return intent

    def get_intent(self, intent_id: str) -> Optional[EnergySavingIntent]:
        """Get intent by ID."""
        logger.info(f"[get_intent] Looking for {intent_id} in memory: {list(self._intents.keys())}")
        logger.info(f"[get_intent] File path: {self._intents_file}")
        if os.path.exists(self._intents_file):
            try:
                with open(self._intents_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"[get_intent] File contents keys: {list(data.keys())}")
                    for intent_id_f, intent_data in data.items():
                        if intent_id_f not in self._intents:
                            intent = EnergySavingIntent(**intent_data)
                            self._intents[intent_id_f] = intent
                            logger.info(f"[get_intent] Loaded intent {intent_id_f} from file into memory")
            except Exception as e:
                logger.warning(f"[get_intent] Failed to read file: {e}")
        result = self._intents.get(intent_id)
        logger.info(f"[get_intent] Result: {result}")
        return result

    def list_intents(self, region: Optional[str] = None) -> List[EnergySavingIntent]:
        """List all intents, optionally filtered by region."""
        intents = list(self._intents.values())
        if region:
            intents = [i for i in intents if i.region.value == region]
        return intents

    # Electricity Price
    def get_electricity_price(self, region: str) -> ElectricityPriceResponse:
        """Get electricity price for region (with caching)."""
        # Check cache first
        if region in self._price_cache:
            cached = self._price_cache[region]
            if datetime.now() < cached.valid_until:
                return ElectricityPriceResponse(
                    region=region,
                    current_price=cached.time_slot_prices[0].price if cached.time_slot_prices else 0.0,
                    time_slots=cached.time_slot_prices,
                    bands=cached.price_bands,
                    valid_until=cached.valid_until,
                )

        # Create new price data (mock - in real impl, call external API)
        price_data = ElectricityPriceData(
            region=region,
            valid_until=datetime.now() + timedelta(minutes=5),
            time_slot_prices=DEFAULT_TIME_SLOT_PRICES,
            price_bands=DEFAULT_PRICE_BANDS,
        )
        self._price_cache[region] = price_data

        return ElectricityPriceResponse(
            region=region,
            current_price=price_data.time_slot_prices[0].price,
            time_slots=price_data.time_slot_prices,
            bands=price_data.price_bands,
            valid_until=price_data.valid_until,
        )

    # Band/Site Classification
    def classify_site(self, site_id: str, current_power_kw: float) -> SiteClassification:
        """Classify a single site into power band."""
        current_band = classify_band_fn(current_power_kw)
        
        # For now, target band is same as current (simplified)
        # In real impl, this would consider electricity prices and strategies
        target_band = current_band
        
        classification = classify_site_fn(current_band, target_band)
        
        return SiteClassification(
            site_id=site_id,
            current_band=current_band,
            classified_band=target_band,
            classification=classification,
            classification_reason=f"Power consumption {current_power_kw}KW classified to band {current_band}",
            energy_saving_potential_kw=0.0,  # Simplified
            confidence_score=0.9,
        )

    def classify_cluster(self, cluster_id: str, sites: List[Dict[str, Any]]) -> ClusterClassificationResult:
        """Classify all sites in a cluster."""
        downgrade = []
        upgrade = []
        stable = []
        total_saving = 0.0

        for site_data in sites:
            site_id = site_data["site_id"]
            current_power_kw = site_data.get("current_power_kw", 2.0)
            
            classification = self.classify_site(site_id, current_power_kw)
            
            if classification.classification == SiteClass.DOWNGRADE:
                downgrade.append(classification)
                total_saving += classification.energy_saving_potential_kw
            elif classification.classification == SiteClass.UPGRADE:
                upgrade.append(classification)
            else:
                stable.append(classification)

        return ClusterClassificationResult(
            cluster_id=cluster_id,
            total_sites=len(sites),
            downgrade_sites=downgrade,
            upgrade_sites=upgrade,
            stable_sites=stable,
            estimated_total_saving_kw=total_saving,
        )

    # Cluster Optimization
    def optimize_cluster(
        self,
        cluster_id: str,
        classification_result: ClusterClassificationResult,
        target: str = "maximized_saving",
    ) -> ClusterOptimizationPlan:
        """Generate cluster optimization plan."""
        plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
        
        migration_out = []
        migration_in = []

        # Generate migration actions for DOWNGRADE sites
        for site in classification_result.downgrade_sites:
            migration_out.append(TrafficMigrationAction(
                site_id=site.site_id,
                action_type="decrease_power",
                parameter_value=3.0,  # Reduce 3dB
                execution_window="23~5",  # During low demand
                priority=5,
            ))

        # Generate migration actions for UPGRADE sites
        for site in classification_result.upgrade_sites:
            migration_out.append(TrafficMigrationAction(
                site_id=site.site_id,
                action_type="increase_power",
                parameter_value=2.0,  # Increase 2dB
                execution_window="6~9",  # During morning
                priority=5,
            ))

        # Calculate expected cost reduction (simplified)
        expected_reduction = len(classification_result.downgrade_sites) * 2.5

        return ClusterOptimizationPlan(
            plan_id=plan_id,
            cluster_id=cluster_id,
            optimization_horizon="monthly",
            migration_out_actions=migration_out,
            migration_in_actions=migration_in,
            expected_cost_reduction_percent=expected_reduction,
            risk_assessment={
                "coverage_risk": 0.1,
                "experience_risk": 0.05,
            },
            status="pending",
        )

    # MAE Negotiation
    def negotiate_with_mae(self, plan: ClusterOptimizationPlan, intent: EnergySavingIntent) -> NegotiationResponse:
        """Negotiate with MAE via A2A-T."""
        import asyncio
        from workflow_engine import WorkflowEngineClient
        
        negotiation_id = f"NEG-{uuid.uuid4().hex[:8].upper()}"
        
        try:
            orch_url = os.environ.get("ORCHESTRATE_URL", "http://127.0.0.1:5001")
            mae_url = os.environ.get("MAE_AGENT_URL", "http://127.0.0.1:8898")
            
            logger.info(f"[EnergyAgent] Negotiating with MAE at {mae_url}")
            
            request_data = {
                "plan_id": plan.plan_id,
                "cluster_id": plan.cluster_id,
                "expected_cost_reduction_percent": plan.expected_cost_reduction_percent,
                "risk_assessment": plan.risk_assessment,
                "intent": {
                    "intent_id": intent.intent_id,
                    "region": intent.region.value if hasattr(intent.region, 'value') else intent.region,
                    "energy_target": intent.energy_target.value if hasattr(intent.energy_target, 'value') else intent.energy_target,
                    "safeguard": {
                        "min_throughput_mbps": intent.safeguard.min_throughput_mbps,
                        "max_latency_ms": intent.safeguard.max_latency_ms,
                        "coverage_maintain": intent.safeguard.coverage_maintain,
                    }
                }
            }
            
            client = WorkflowEngineClient(base_url=mae_url, ssl_verify=False)
            response = asyncio.run(client.send_task(
                task_name="negotiation_request",
                agent_name="MAE Agent",
                user_input=json.dumps(request_data),
            ))
            
            if response and response.get("result"):
                result = json.loads(response["result"])
                return NegotiationResponse(
                    achievable=result.get("achievable", True),
                    constraints=result.get("constraints", {
                        "max_power_reduction_percent": 15,
                        "min_throughput_mbps": intent.safeguard.min_throughput_mbps,
                        "execution_window_hours": [23, 0, 1, 2, 3, 4],
                    }),
                    risk_factors=result.get("risk_factors", []),
                    negotiation_id=result.get("negotiation_id", negotiation_id),
                )
            
        except Exception as e:
            logger.warning(f"[EnergyAgent] MAE negotiation failed: {e}, using fallback")
        
        return NegotiationResponse(
            achievable=True,
            constraints={
                "max_power_reduction_percent": 15,
                "min_throughput_mbps": intent.safeguard.min_throughput_mbps,
                "execution_window_hours": [23, 0, 1, 2, 3, 4],
            },
            risk_factors=["coverage_degradation_risk", "user_experience_impact_risk"],
            negotiation_id=negotiation_id,
        )


# Singleton instance
_energy_agent_instance: Optional[EnergyAgent] = None


def get_energy_agent() -> EnergyAgent:
    """Get singleton Energy Agent instance."""
    global _energy_agent_instance
    if _energy_agent_instance is None:
        _energy_agent_instance = EnergyAgent()
    return _energy_agent_instance
