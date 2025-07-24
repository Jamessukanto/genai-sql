import streamlit as st
import requests

# --- Configuration ---
BASE_URL = "http://backend:8000"
USER = "superuser"

# --- Page Setup ---
st.set_page_config(page_title="💬 Chat Assistant", layout="wide", initial_sidebar_state="expanded")

# --- Title ---
st.title("SQL Chat Assistant Demo")

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Token management ---
if "current_fleet_id" not in st.session_state:
    st.session_state.current_fleet_id = None
if "current_token" not in st.session_state:
    st.session_state.current_token = None


# --- Helpers ---
def append_message(role, content):
    """Append a message to the session state messages."""
    st.session_state.messages.append({"type": role, "content": content})


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


# --- Sidebar with eager token generation ---
with st.sidebar:
    st.header("Configuration")
    fleet_id = st.selectbox("Select Fleet ID", options=["1", "2"])
    
    # Generate token immediately when fleet_id changes OR if no token exists
    if (fleet_id != st.session_state.current_fleet_id or 
        st.session_state.current_token is None):
        generate_token(fleet_id)
        st.success(f"✅ Access granted to Fleet {fleet_id}")


# --- Chat Input ---
query = st.chat_input("Type your message here...")
if query:
    append_message("human", query)

    try:
        with st.spinner("Thinking..."):
            token = st.session_state.current_token

            chat_response = make_api_call("api/chat/execute_user_query", {
                "messages": st.session_state.messages,
                "query": query
            }, token)

            reply = chat_response["response"]
            append_message("ai", reply)

    except Exception as e:
        st.error(str(e))


# --- Render Chat ---
for message in st.session_state.messages:
    if message["type"] == "system":
        continue
    with st.chat_message("user" if message["type"] == "human" else "assistant"):
        st.markdown(message["content"])

