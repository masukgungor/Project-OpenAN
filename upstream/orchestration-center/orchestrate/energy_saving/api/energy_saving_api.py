from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from orchestrate.energy_saving.models import (
    EnergySavingIntent,
    EnergySavingIntentCreate,
    EnergySavingIntentResponse,
    ElectricityPriceResponse,
    SiteClassification,
    ClusterClassificationResult,
    ClusterOptimizationPlan,
    NegotiationResponse,
)
from orchestrate.energy_saving.agents import get_energy_agent

router = APIRouter(prefix="/rest/v1/orchestrate/energy-saving", tags=["Energy Saving"])

# Request/Response models
class SiteData(BaseModel):
    site_id: str
    current_power_kw: float = 2.0


class ClassifySiteRequest(BaseModel):
    site_id: str
    current_power_kw: float


class ClassifyClusterRequest(BaseModel):
    cluster_id: str
    sites: List[SiteData]


class OptimizeClusterRequest(BaseModel):
    cluster_id: str
    classification_result: ClusterClassificationResult
    target: str = "maximized_saving"


class ExecutePlanRequest(BaseModel):
    plan_id: str


# Intent Endpoints
@router.post("/intent", response_model=EnergySavingIntentResponse)
async def create_intent(intent_create: EnergySavingIntentCreate):
    """Create a new energy saving intent."""
    agent = get_energy_agent()
    intent = agent.create_intent(intent_create)
    return EnergySavingIntentResponse(
        intent_id=intent.intent_id,
        region=intent.region,
        energy_target=intent.energy_target,
        safeguard=intent.safeguard,
        created_at=intent.created_at,
        validity_period=intent.validity_period,
        priority=intent.priority,
        cluster_id=intent.cluster_id,
        status=intent.status,
        source=getattr(intent, 'source', 'form'),
    )


@router.get("/intent/{intent_id}", response_model=EnergySavingIntentResponse)
async def get_intent(intent_id: str):
    """Get energy saving intent by ID."""
    agent = get_energy_agent()
    intent = agent.get_intent(intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail=f"Intent {intent_id} not found")
    return EnergySavingIntentResponse(
        intent_id=intent.intent_id,
        region=intent.region,
        energy_target=intent.energy_target,
        safeguard=intent.safeguard,
        created_at=intent.created_at,
        validity_period=intent.validity_period,
        priority=intent.priority,
        cluster_id=intent.cluster_id,
        status=intent.status,
        source=getattr(intent, 'source', 'form'),
    )


@router.get("/intents", response_model=List[EnergySavingIntentResponse])
async def list_intents(region: Optional[str] = Query(None)):
    """List all energy saving intents."""
    agent = get_energy_agent()
    intents = agent.list_intents(region)
    return [
        EnergySavingIntentResponse(
            intent_id=i.intent_id,
            region=i.region,
            energy_target=i.energy_target,
            safeguard=i.safeguard,
            created_at=i.created_at,
            validity_period=i.validity_period,
            priority=i.priority,
            cluster_id=i.cluster_id,
            status=i.status,
            source=getattr(i, 'source', 'form'),
        )
        for i in intents
    ]


# Electricity Price Endpoints
class ElectricityPriceRequest(BaseModel):
    region: str

@router.post("/electricity-price", response_model=ElectricityPriceResponse)
async def get_electricity_price(request: ElectricityPriceRequest):
    """Get electricity price for region."""
    agent = get_energy_agent()
    return agent.get_electricity_price(request.region)


# Classification Endpoints
@router.post("/classify-site", response_model=SiteClassification)
async def classify_site(request: ClassifySiteRequest):
    """Classify a single site into power band."""
    agent = get_energy_agent()
    return agent.classify_site(request.site_id, request.current_power_kw)


@router.post("/classify-cluster", response_model=ClusterClassificationResult)
async def classify_cluster(request: ClassifyClusterRequest):
    """Classify all sites in a cluster."""
    agent = get_energy_agent()
    sites_data = [{"site_id": s.site_id, "current_power_kw": s.current_power_kw} for s in request.sites]
    return agent.classify_cluster(request.cluster_id, sites_data)


# Optimization Endpoints
@router.post("/optimize-cluster", response_model=ClusterOptimizationPlan)
async def optimize_cluster(request: OptimizeClusterRequest):
    """Generate cluster optimization plan."""
    agent = get_energy_agent()
    return agent.optimize_cluster(request.cluster_id, request.classification_result, request.target)


# MAE Negotiation Endpoint
@router.post("/negotiate", response_model=NegotiationResponse)
async def negotiate_with_mae(request: ExecutePlanRequest):
    """Negotiate with MAE via A2A-T."""
    agent = get_energy_agent()
    
    # For now, we need intent_id to get the intent details
    # This is a simplified version - real impl would be more complex
    intents = agent.list_intents()
    if not intents:
        raise HTTPException(status_code=400, detail="No intents found. Create an intent first.")
    
    latest_intent = intents[-1]
    
    # Create a mock plan for negotiation
    mock_plan = ClusterOptimizationPlan(
        plan_id=request.plan_id,
        cluster_id=latest_intent.cluster_id or "DEFAULT",
        expected_cost_reduction_percent=10.0,
        risk_assessment={"coverage_risk": 0.1, "experience_risk": 0.05},
    )
    
    return agent.negotiate_with_mae(mock_plan, latest_intent)


# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "energy-saving"}


# LLM-based Intent Generation
class GenerateIntentRequest(BaseModel):
    description: str
    region: Optional[str] = None


@router.post("/generate-intent", response_model=EnergySavingIntentResponse)
async def generate_intent_from_description(request: GenerateIntentRequest):
    """Generate energy saving intent from natural language description using LLM."""
    from common.llm import get_llm_instance
    import json
    
    llm = get_llm_instance("chat")
    
    system_prompt = """You are an Energy Saving Intent Generator. Based on the user's natural language description,
generate a structured energy saving intent in JSON format.

Available regions: north, south, east, west, central
Energy targets: maximized_saving, proactive_saving, balanced, experience_first
Priority: 1-10 (1=lowest, 10=highest)

Return ONLY valid JSON with these fields:
- region: string (pick best matching region or use "north" as default)
- energy_target: string (infer from description: "maximize saving" → maximized_saving, "balanced" → balanced, etc.)
- priority: integer 1-10 (default to 5 if not specified)
- cluster_id: string (optional, can be empty string)
- safeguard.min_throughput_mbps: float (default 10)
- safeguard.max_latency_ms: float (default 50)
- safeguard.coverage_maintain: boolean (default true)
- validity_period.start: string (HH:MM format, default "00:00")
- validity_period.end: string (HH:MM format, default "23:59")

Example: {"region": "north", "energy_target": "maximized_saving", "priority": 7, "cluster_id": "", "safeguard": {"min_throughput_mbps": 10, "max_latency_ms": 50, "coverage_maintain": true}, "validity_period": {"start": "00:00", "end": "23:59"}}"""

    user_prompt = f"{system_prompt}\n\nUser request: Generate an energy saving intent for: {request.description}"
    
    if request.region:
        user_prompt += f"\n\nPreferred region: {request.region}"
    
    reasoning, result = llm.ask_llm(prompt=user_prompt)
    
    try:
        json_str = result.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        json_str = json_str.strip()
        intent_data = json.loads(json_str)
        
        from orchestrate.energy_saving.models.energy_intent import Region, EnergySavingTarget
        region_val = intent_data.get("region", "north")
        if isinstance(region_val, str):
            region_val = Region(region_val)
        
        target_val = intent_data.get("energy_target", "maximized_saving")
        if isinstance(target_val, str):
            target_val = EnergySavingTarget(target_val)
        
        intent_create = EnergySavingIntentCreate(
            region=region_val,
            energy_target=target_val,
            priority=intent_data.get("priority", 5),
            cluster_id=intent_data.get("cluster_id", ""),
            safeguard=intent_data.get("safeguard", {
                "min_throughput_mbps": 10,
                "max_latency_ms": 50,
                "coverage_maintain": True
            }),
            validity_period=intent_data.get("validity_period", {
                "start": "00:00",
                "end": "23:59"
            }),
            source="llm"
        )
        
        agent = get_energy_agent()
        intent = agent.create_intent(intent_create)
        logger.info(f"[generate-intent] Intent created: {intent.intent_id}, source={intent.source}")
        response = EnergySavingIntentResponse(
            intent_id=intent.intent_id,
            region=intent.region,
            energy_target=intent.energy_target,
            safeguard=intent.safeguard,
            created_at=intent.created_at,
            validity_period=intent.validity_period,
            priority=intent.priority,
            cluster_id=intent.cluster_id,
            status=intent.status,
            source=intent.source,
        )
        logger.info(f"[generate-intent] Response model: {response.model_dump()}")
        return response
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {result}")
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {result[:500]}, error: {str(e)}")
    except Exception as e:
        logger.error(f"Intent creation error: {result}")
        raise HTTPException(status_code=500, detail=f"Failed to create intent: {str(e)}, LLM result: {result[:500]}")
