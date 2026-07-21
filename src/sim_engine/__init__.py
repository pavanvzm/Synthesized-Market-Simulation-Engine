"""Synthesized Market Simulation Engine"""

__version__ = "0.1.0"
__author__ = "Meta AI Engineering"

from sim_engine.config import Config
from sim_engine.personas import Persona, ConsumerPersona, CompetitorPersona

__all__ = [
    "Config",
    "Persona",
    "ConsumerPersona",
    "CompetitorPersona",
]
