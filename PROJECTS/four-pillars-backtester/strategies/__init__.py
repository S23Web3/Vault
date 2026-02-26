"""
Strategy plugin system for Vince ML agent.
Strategies are loaded by name. Each strategy provides its own
indicator enrichment, signal generation, feature extraction, and labeling.
"""

from pathlib import Path
import importlib


STRATEGY_DIR = Path(__file__).resolve().parent

_REGISTRY = {
    "four_pillars": "strategies.four_pillars",
}


def load_strategy(name: str = "four_pillars"):
    """Load a strategy plugin by name and return an instance."""
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError("Unknown strategy: " + name + ". Available: " + available)
    module = importlib.import_module(_REGISTRY[name])
    return module.create_plugin()


def list_strategies() -> list:
    """Return list of available strategy names."""
    return sorted(_REGISTRY.keys())
