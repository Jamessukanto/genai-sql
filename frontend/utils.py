import streamlit as st
import requests
import os

# --- Configuration ---
# Get backend URL from environment variable (for Render) or use default (for local development)
BASE_URL = os.getenv("BACKEND_URL", "https://genai-sql-2.onrender.com")
print()
print()
print()
print()
print()
print()
print()
print()
print()
print(BASE_URL)
USER = "end_user"

# --- Sample Questions ---
SAMPLE_QUESTIONS = [
    "What is the SOC of vehicle GBM6296G right now?",
    "How many SRM T3 EVs are in my fleet?",
    "What is the fleet‑wide average SOC comfort zone?"
]

# --- Helpers ---
def append_message(role, content):
    """Append a message to the session state messages."""
    st.session_state.messages.append({"type": role, "content": content})

def truncate_text(text, max_length=38):
    """Truncate text to max_length with ellipsis if longer."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def make_api_call(endpoint, body=None, token=None, timeout=60):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        res = requests.post(
            f"{BASE_URL}/{endpoint}",
            json=body,
            headers=headers,
            timeout=timeout
        )
        if not res.ok:
            raise Exception(res.text)
        return res.json()
    except requests.exceptions.Timeout:
        raise Exception(f"Request to {endpoint} timed out after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")

def generate_token(fleet_id):
    """Generate a new token for the given fleet_id."""
    token_response = make_api_call("api/auth/generate_jwt_token", {
        "sub": USER,
        "fleet_id": fleet_id,
        "exp_hours": 1
    })
    
    # Update session state
    st.session_state.current_token = token_response["token"]
    st.session_state.current_fleet_id = fleet_id
    
    return st.session_state.current_token 