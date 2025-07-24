import os, yaml
from typing import Dict, Any

MODELS = {
    "medium": "mistral-medium-latest",
    "small": "mistral-small-latest", 
    "tiny": "mistral-tiny-latest",
    "llama3-70b": "llama3-70b-8192"
}

# Model configurations for API calls
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    MODELS["medium"]: {
        "model": MODELS["medium"],
        "temperature": 0,
        "max_tokens": 4096,  # Example, adjust based on model limits
        "timeout": 60,  # Timeout in seconds
    },
    MODELS["small"]: {
        "model": MODELS["small"],
        "temperature": 0,
        "max_tokens": 4096,
        "timeout": 45,  # Timeout in seconds
    },
    MODELS["tiny"]: {
        "model": MODELS["tiny"],
        "temperature": 0,
        "max_tokens": 4096,
        "timeout": 30,  # Timeout in seconds
    },
    MODELS["llama3-70b"]: {
        "model": MODELS["llama3-70b"],
        "temperature": 0,
        "max_tokens": 8192,  
        "timeout": 45,  
    }
}

DEFAULT_MODEL = MODELS["medium"]

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

