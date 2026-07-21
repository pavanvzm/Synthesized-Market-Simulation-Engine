"""Configuration management for the simulation engine."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class ResourceProfile:
    """Resource profile settings."""
    persona_count: int = 20
    sim_rounds: int = 3
    llm_max_tokens: int = 96
    memory_top_k: int = 2
    batch_size: int = 4
    debate_enabled: bool = False
    debate_entropy_threshold: float = 0.85
    qdrant_mode: str = "local"


LOW_PROFILE = ResourceProfile(
    persona_count=20,
    sim_rounds=3,
    llm_max_tokens=96,
    memory_top_k=2,
    batch_size=4,
    debate_enabled=False,
    qdrant_mode="local",
)

BALANCED_PROFILE = ResourceProfile(
    persona_count=100,
    sim_rounds=6,
    llm_max_tokens=160,
    memory_top_k=3,
    batch_size=8,
    debate_enabled=True,
    qdrant_mode="local",
)

HIGH_PROFILE = ResourceProfile(
    persona_count=300,
    sim_rounds=10,
    llm_max_tokens=256,
    memory_top_k=5,
    batch_size=16,
    debate_enabled=True,
    qdrant_mode="server",
)


@dataclass
class Config:
    """Main configuration class."""
    
    resource_profile: str = "low"
    llm_provider: str = "mock"
    persona_count: int = 20
    consumer_ratio: float = 0.8
    sim_rounds: int = 3
    random_seed: int = 42
    llm_max_tokens: int = 96
    llm_temperature: float = 0.7
    memory_top_k: int = 2
    qdrant_mode: str = "local"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    collection_name: str = "persona_memory"
    batch_size: int = 4
    debate_enabled: bool = False
    debate_entropy_threshold: float = 0.85
    cache_dir: str = ".cache"
    cache_ttl_hours: int = 24
    output_dir: str = "data/sim/runs"
    log_level: str = "INFO"
    
    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        # Apply resource profile defaults if specified
        if "resource_profile" in data:
            profile = data["resource_profile"]
            if profile == "low":
                defaults = LOW_PROFILE
            elif profile == "balanced":
                defaults = BALANCED_PROFILE
            elif profile == "high":
                defaults = HIGH_PROFILE
            else:
                defaults = LOW_PROFILE
            
            # Merge profile defaults with explicit config
            config_dict = {
                "persona_count": defaults.persona_count,
                "sim_rounds": defaults.sim_rounds,
                "llm_max_tokens": defaults.llm_max_tokens,
                "memory_top_k": defaults.memory_top_k,
                "batch_size": defaults.batch_size,
                "debate_enabled": defaults.debate_enabled,
                "qdrant_mode": defaults.qdrant_mode,
            }
            config_dict.update(data)
            return cls(**config_dict)
        
        return cls(**data) if data else cls()
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()
        
        profile = os.getenv("RESOURCE_PROFILE", "low")
        if profile == "low":
            defaults = LOW_PROFILE
        elif profile == "balanced":
            defaults = BALANCED_PROFILE
        elif profile == "high":
            defaults = HIGH_PROFILE
        else:
            defaults = LOW_PROFILE
        
        return cls(
            resource_profile=os.getenv("RESOURCE_PROFILE", "low"),
            llm_provider=os.getenv("LLM_PROVIDER", "mock"),
            persona_count=int(os.getenv("PERSONA_COUNT", defaults.persona_count)),
            sim_rounds=int(os.getenv("SIM_ROUNDS", defaults.sim_rounds)),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", defaults.llm_max_tokens)),
            memory_top_k=int(os.getenv("MEMORY_TOP_K", defaults.memory_top_k)),
            batch_size=int(os.getenv("BATCH_SIZE", defaults.batch_size)),
            debate_enabled=os.getenv("DEBATE_ENABLED", str(defaults.debate_enabled)).lower() == "true",
            qdrant_mode=os.getenv("QDRANT_MODE", defaults.qdrant_mode),
            qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
            random_seed=int(os.getenv("RANDOM_SEED", "42")),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "resource_profile": self.resource_profile,
            "llm_provider": self.llm_provider,
            "persona_count": self.persona_count,
            "consumer_ratio": self.consumer_ratio,
            "sim_rounds": self.sim_rounds,
            "random_seed": self.random_seed,
            "llm_max_tokens": self.llm_max_tokens,
            "llm_temperature": self.llm_temperature,
            "memory_top_k": self.memory_top_k,
            "qdrant_mode": self.qdrant_mode,
            "qdrant_host": self.qdrant_host,
            "qdrant_port": self.qdrant_port,
            "collection_name": self.collection_name,
            "batch_size": self.batch_size,
            "debate_enabled": self.debate_enabled,
            "debate_entropy_threshold": self.debate_entropy_threshold,
            "cache_dir": self.cache_dir,
            "cache_ttl_hours": self.cache_ttl_hours,
            "output_dir": self.output_dir,
            "log_level": self.log_level,
        }
    
    def get_output_path(self, run_id: str) -> Path:
        """Get output directory path for a run."""
        return Path(self.output_dir) / run_id
    
    def ensure_dirs(self) -> None:
        """Ensure all required directories exist."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
