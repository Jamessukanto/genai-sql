from typing import Dict, Any

# Available Mistral models
MISTRAL_MODELS = {
    "medium": "mistral-medium-latest",
    "small": "mistral-small-latest", 
    "tiny": "mistral-tiny-latest"
}

# Model configurations for API calls
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    MISTRAL_MODELS["medium"]: {
        "model": MISTRAL_MODELS["medium"],
        "temperature": 0,
        "max_tokens": 4096,  # Example, adjust based on model limits
    },
    MISTRAL_MODELS["small"]: {
        "model": MISTRAL_MODELS["small"],
        "temperature": 0,
        "max_tokens": 4096,
    },
    MISTRAL_MODELS["tiny"]: {
        "model": MISTRAL_MODELS["tiny"],
        "temperature": 0,
        "max_tokens": 4096,
    }
}

# Timeout configurations (in seconds) for local request handling
TIMEOUT_CONFIGS = {
    MISTRAL_MODELS["medium"]: 60,
    MISTRAL_MODELS["small"]: 45,
    MISTRAL_MODELS["tiny"]: 30,
}

DEFAULT_MODEL = MISTRAL_MODELS["medium"]

def get_model_config(model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """Get API configuration for specified model."""
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS[DEFAULT_MODEL])

def get_timeout(model_name: str = DEFAULT_MODEL) -> int:
    """Get timeout configuration for specified model."""
    return TIMEOUT_CONFIGS.get(model_name, TIMEOUT_CONFIGS[DEFAULT_MODEL]) 