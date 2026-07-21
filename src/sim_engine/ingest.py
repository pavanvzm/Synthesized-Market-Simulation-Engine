"""Data ingestion module for market events, products, and competitors."""

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class MarketEvent(BaseModel):
    """Market event model."""
    event_id: str
    event_type: str  # price_change, feature_update, marketing_campaign, competitor_action
    timestamp: str
    source: str
    description: str
    impact_score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Product(BaseModel):
    """Product model."""
    product_id: str
    name: str
    category: str
    price: float
    features: list[str] = Field(default_factory=list)
    target_segment: str


class Competitor(BaseModel):
    """Competitor model."""
    competitor_id: str
    name: str
    market_share: float = Field(ge=0.0, le=1.0)
    primary_products: list[str] = Field(default_factory=list)
    pricing_strategy: str  # premium, competitive, discount
    recent_actions: list[str] = Field(default_factory=list)


class Ingestor:
    """Data ingestion handler."""

    def __init__(self):
        self.events: list[MarketEvent] = []
        self.products: list[Product] = []
        self.competitors: list[Competitor] = []

    def ingest_csv(self, path: str, data_type: str) -> int:
        """Ingest data from CSV file.
        
        Args:
            path: Path to CSV file
            data_type: Type of data (events, products, competitors)
        
        Returns:
            Number of records ingested
        """
        df = pd.read_csv(path)
        count = 0

        if data_type == "events":
            for _, row in df.iterrows():
                event = MarketEvent(
                    event_id=row.get("event_id", f"evt_{count}"),
                    event_type=row.get("event_type", "unknown"),
                    timestamp=row.get("timestamp", ""),
                    source=row.get("source", "csv"),
                    description=row.get("description", ""),
                    impact_score=float(row.get("impact_score", 0.5)),
                )
                self.events.append(event)
                count += 1

        elif data_type == "products":
            for _, row in df.iterrows():
                product = Product(
                    product_id=row.get("product_id", f"prod_{count}"),
                    name=row.get("name", "Unknown"),
                    category=row.get("category", "general"),
                    price=float(row.get("price", 0)),
                    features=self._parse_list(row.get("features", "")),
                    target_segment=row.get("target_segment", "mass"),
                )
                self.products.append(product)
                count += 1

        elif data_type == "competitors":
            for _, row in df.iterrows():
                competitor = Competitor(
                    competitor_id=row.get("competitor_id", f"comp_{count}"),
                    name=row.get("name", "Unknown"),
                    market_share=float(row.get("market_share", 0.1)),
                    primary_products=self._parse_list(row.get("products", "")),
                    pricing_strategy=row.get("pricing_strategy", "competitive"),
                    recent_actions=self._parse_list(row.get("recent_actions", "")),
                )
                self.competitors.append(competitor)
                count += 1

        return count

    def ingest_json(self, path: str, data_type: str) -> int:
        """Ingest data from JSON file.
        
        Args:
            path: Path to JSON file
            data_type: Type of data (events, products, competitors)
        
        Returns:
            Number of records ingested
        """
        with open(path, "r") as f:
            data = json.load(f)

        count = 0
        if isinstance(data, list):
            for item in data:
                self._add_item(item, data_type)
                count += 1
        else:
            self._add_item(data, data_type)
            count = 1

        return count

    def ingest_jsonl(self, path: str, data_type: str) -> int:
        """Ingest data from JSONL file.
        
        Args:
            path: Path to JSONL file
            data_type: Type of data
        
        Returns:
            Number of records ingested
        """
        count = 0
        with open(path, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                self._add_item(data, data_type)
                count += 1
        return count

    def _add_item(self, data: dict[str, Any], data_type: str) -> None:
        """Add item to appropriate collection."""
        if data_type == "events":
            event = MarketEvent(**data)
            self.events.append(event)
        elif data_type == "products":
            product = Product(**data)
            self.products.append(product)
        elif data_type == "competitors":
            competitor = Competitor(**data)
            self.competitors.append(competitor)

    def _parse_list(self, value: Any) -> list[str]:
        """Parse string or list into list of strings."""
        if isinstance(value, list):
            return [str(v) for v in value]
        if isinstance(value, str):
            if value.startswith("[") and value.endswith("]"):
                # Parse JSON-like array
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            # Split by comma or semicolon
            return [v.strip() for v in value.replace(";", ",").split(",") if v.strip()]
        return []

    def get_events(self) -> list[MarketEvent]:
        """Get all ingested events."""
        return self.events

    def get_products(self) -> list[Product]:
        """Get all ingested products."""
        return self.products

    def get_competitors(self) -> list[Competitor]:
        """Get all ingested competitors."""
        return self.competitors

    def to_dict(self) -> dict[str, Any]:
        """Convert all data to dictionary."""
        return {
            "events": [e.model_dump() for e in self.events],
            "products": [p.model_dump() for p in self.products],
            "competitors": [c.model_dump() for c in self.competitors],
        }
