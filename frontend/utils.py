import streamlit as st
import requests
import os

# --- Configuration ---
# Get backend URL from environment variable (for Render) or use default (for local development)
BASE_URL = os.getenv("BACKEND_URL", "https://genai-sql-2.onrender.com")
USER = "end_user"

# --- Sample Questions and Answers ---
SAMPLE_QUESTIONS = [
    "What is the SOC of vehicle GBM6296G right now?",
    "How many SRM T3 EVs are in my fleet?",
    "Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?",
    "What is the fleet-wide average SOC comfort zone?",
    "Which vehicles spent > 20 % time in the 90-100 % SOC band this week?",
    "How many vehicles are currently driving with SOC < 30 %?",
    "What is the total km and driving hours by my fleet over the past 7 days, and which are the most-used & least-used vehicles?",
]

SAMPLE_ANSWERS = [
    "Fleet 1: 57%; Fleet 2: No data",
    "Fleet 1: 2 vehicles; Fleet 2: 0 vehicle",
    "Fleet 1: Yes, GBM6296G; Fleet 2: No data", 
    "Fleet 1: 57.5%, 60.0%", 
    "Fleet 1: GBM6296G; Fleet 2: No data",
    "Fleet 1: 0 vehicle; Fleet 2: 0 vehicle;",   
    "Request user to ask one question at a time",
]

# --- Helpers ---
def append_message(role, content):
    """Append a message to the session state messages."""
    st.session_state.messages.append({"type": role, "content": content})

def truncate_text(text, max_length=42):
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
    import time
    
    # Add a small delay to prevent rapid requests
    time.sleep(0.5)
    
    try:
        token_response = make_api_call("api/auth/generate_jwt_token", {
            "sub": USER,
            "fleet_id": fleet_id,
            "exp_hours": 1
        })
        
        # Update session state
        st.session_state.current_token = token_response["token"]
        st.session_state.current_fleet_id = fleet_id
        
        return st.session_state.current_token
    except Exception as e:
        if "Too Many Requests" in str(e):
            print("Too Many Requests")
            # Wait a bit longer and retry once
            time.sleep(2)
            token_response = make_api_call("api/auth/generate_jwt_token", {
                "sub": USER,
                "fleet_id": fleet_id,
                "exp_hours": 1
            })
            st.session_state.current_token = token_response["token"]
            st.session_state.current_fleet_id = fleet_id
            return st.session_state.current_token
        else:
            raise e

def load_css():
    """Load external CSS file."""
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True) 