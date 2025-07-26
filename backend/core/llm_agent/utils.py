import os, yaml
from typing import Dict, Any

MODELS = {
    "fast": "qwen/qwen3-32b",
    # "fast": "llama-3.1-8b-instant",
    "quality": "llama-3.3-70b-versatile",
}

# Model configurations for API calls
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    MODELS["fast"]: {
        "model": MODELS["fast"],
        "temperature": 0,
        "max_tokens": 4096,
        "timeout": 30,
    },
    MODELS["quality"]: {
        "model": MODELS["quality"],
        "temperature": 0,
        "max_tokens": 4096,
        "timeout": 80,
    },
}

DEFAULT_MODEL = MODELS["quality"]

def get_model_config(model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """Get API configuration for specified model."""
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS[DEFAULT_MODEL])

def load_semantic_map():
    """Loads and formats semantic term mappings from a YAML."""

    file_path = os.path.join(os.path.dirname(__file__), "semantic_map.yaml")
    with open(file_path) as f:
        m = yaml.safe_load(f)

    mappings_str = []
    for term, info in m.items():
        cols = ", ".join(info["columns"])
        mappings_str.append(f"- '{term}'. {info['description']} → [{cols}]")

    return "\n".join(mappings_str)

def handle_empty_results(original_run):
    """
    Wrapper function to handle empty results from database queries.
    Takes the original run function as a parameter to avoid closure issues.
    """
    def wrapper(*args, **kwargs):
        result = original_run(*args, **kwargs)
        if not result or (isinstance(result, list) and len(result) == 0):
            return "No data available for this query."
        return result
    return wrapper

