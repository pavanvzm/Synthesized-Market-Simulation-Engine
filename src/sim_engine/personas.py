"""Persona generation module for synthetic consumers and competitors."""

import random
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """Base persona model."""
    persona_id: str
    persona_type: str  # consumer or competitor
    segment: str
    price_sensitivity: float = Field(ge=0.0, le=1.0)
    feature_preference: list[str] = Field(default_factory=list)
    brand_loyalty: float = Field(ge=0.0, le=1.0)
    income_band: str  # low, medium, high
    channel_preference: str  # online, offline, mixed
    churn_risk: float = Field(ge=0.0, le=1.0)
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    memory_summary: str = ""


class ConsumerPersona(Persona):
    """Consumer persona with additional attributes."""
    persona_type: str = "consumer"
    age_range: str = ""
    occupation: str = ""
    household_size: int = 1
    tech_adoption: str = "mainstream"  # early_adopter, mainstream, laggard


class CompetitorPersona(Persona):
    """Competitor persona with business attributes."""
    persona_type: str = "competitor"
    company_size: str = "medium"  # small, medium, large
    market_position: str = "challenger"  # leader, challenger, follower, nicher
    innovation_rate: float = Field(ge=0.0, le=1.0)
    pricing_aggressiveness: float = Field(ge=0.0, le=1.0)
    product_categories: list[str] = Field(default_factory=list)


# Template data for persona generation
SEGMENTS = ["budget", "value", "premium", "luxury", "enterprise"]
INCOME_BANDS = ["low", "medium", "high"]
CHANNEL_PREFS = ["online", "offline", "mixed"]
AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
OCCUPATIONS = ["student", "professional", "manager", "entrepreneur", "retired"]
TECH_ADOPTIONS = ["early_adopter", "mainstream", "laggard"]
COMPANY_SIZES = ["small", "medium", "large"]
MARKET_POSITIONS = ["leader", "challenger", "follower", "nicher"]
FEATURE_CATEGORIES = ["quality", "price", "convenience", "innovation", "support"]


class PersonaGenerator:
    """Generate synthetic personas."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.rng = random.Random(seed)
    
    def generate_consumer(self, override: Optional[dict[str, Any]] = None) -> ConsumerPersona:
        """Generate a consumer persona.
        
        Args:
            override: Optional field overrides
        
        Returns:
            ConsumerPersona instance
        """
        segment = self.rng.choice(SEGMENTS)
        
        # Price sensitivity inversely related to segment
        price_sensitivity_map = {
            "budget": 0.9,
            "value": 0.7,
            "premium": 0.4,
            "luxury": 0.2,
            "enterprise": 0.3,
        }
        base_sensitivity = price_sensitivity_map.get(segment, 0.5)
        price_sensitivity = min(1.0, max(0.0, base_sensitivity + self.rng.uniform(-0.1, 0.1)))
        
        # Brand loyalty varies by segment
        brand_loyalty = 0.3 + self.rng.uniform(0, 0.5) if segment in ["premium", "luxury"] else 0.2 + self.rng.uniform(0, 0.3)
        
        # Churn risk based on price sensitivity and loyalty
        churn_risk = (price_sensitivity * 0.4 + (1 - brand_loyalty) * 0.6) * self.rng.uniform(0.8, 1.2)
        churn_risk = min(1.0, max(0.0, churn_risk))
        
        persona = ConsumerPersona(
            persona_id=f"cons_{uuid4().hex[:8]}",
            segment=segment,
            price_sensitivity=round(price_sensitivity, 2),
            feature_preference=self.rng.sample(FEATURE_CATEGORIES, k=self.rng.randint(1, 3)),
            brand_loyalty=round(brand_loyalty, 2),
            income_band=self.rng.choice(INCOME_BANDS),
            channel_preference=self.rng.choice(CHANNEL_PREFS),
            churn_risk=round(churn_risk, 2),
            goals=["save money", "get quality", "convenience"][:self.rng.randint(1, 3)],
            constraints=["budget limit", "time constraint"][:self.rng.randint(0, 2)],
            age_range=self.rng.choice(AGE_RANGES),
            occupation=self.rng.choice(OCCUPATIONS),
            household_size=self.rng.randint(1, 5),
            tech_adoption=self.rng.choice(TECH_ADOPTIONS),
            memory_summary="New consumer persona initialized.",
        )
        
        if override:
            return type("ConsumerPersona", (ConsumerPersona,), {})(**{**persona.model_dump(), **override})
        
        return persona
    
    def generate_competitor(self, override: Optional[dict[str, Any]] = None) -> CompetitorPersona:
        """Generate a competitor persona.
        
        Args:
            override: Optional field overrides
        
        Returns:
            CompetitorPersona instance
        """
        market_position = self.rng.choice(MARKET_POSITIONS)
        
        # Innovation rate based on position
        innovation_map = {
            "leader": 0.7,
            "challenger": 0.8,
            "follower": 0.4,
            "nicher": 0.6,
        }
        innovation_rate = min(1.0, max(0.0, innovation_map.get(market_position, 0.5) + self.rng.uniform(-0.1, 0.1)))
        
        # Pricing aggressiveness
        pricing_agg = 0.5 + self.rng.uniform(-0.3, 0.3) if market_position == "challenger" else 0.3 + self.rng.uniform(-0.2, 0.2)
        pricing_aggressiveness = min(1.0, max(0.0, pricing_agg))
        
        persona = CompetitorPersona(
            persona_id=f"comp_{uuid4().hex[:8]}",
            segment=self.rng.choice(SEGMENTS),
            price_sensitivity=round(self.rng.uniform(0.3, 0.8), 2),
            feature_preference=self.rng.sample(FEATURE_CATEGORIES, k=self.rng.randint(2, 4)),
            brand_loyalty=round(self.rng.uniform(0.5, 0.9), 2),
            income_band="high",
            channel_preference="mixed",
            churn_risk=round(self.rng.uniform(0.1, 0.4), 2),
            goals=["gain market share", "increase revenue", "innovate"][:self.rng.randint(1, 3)],
            constraints=["budget", "regulatory", "capacity"][:self.rng.randint(1, 2)],
            company_size=self.rng.choice(COMPANY_SIZES),
            market_position=market_position,
            innovation_rate=round(innovation_rate, 2),
            pricing_aggressiveness=round(pricing_aggressiveness, 2),
            product_categories=self.rng.sample(["electronics", "software", "services", "hardware"], k=self.rng.randint(1, 3)),
            memory_summary="New competitor persona initialized.",
        )
        
        if override:
            return type("CompetitorPersona", (CompetitorPersona,), {})(**{**persona.model_dump(), **override})
        
        return persona
    
    def generate_batch(
        self,
        count: int,
        consumer_ratio: float = 0.8,
    ) -> list[Persona]:
        """Generate a batch of personas.
        
        Args:
            count: Total number of personas
            consumer_ratio: Ratio of consumers (0.0-1.0)
        
        Returns:
            List of Persona instances
        """
        personas = []
        consumer_count = int(count * consumer_ratio)
        competitor_count = count - consumer_count
        
        for _ in range(consumer_count):
            personas.append(self.generate_consumer())
        
        for _ in range(competitor_count):
            personas.append(self.generate_competitor())
        
        self.rng.shuffle(personas)
        return personas
