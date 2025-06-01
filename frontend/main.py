import streamlit as st
import requests

# --- Configuration ---
BASE_URL = "http://localhost:8000/api"  # Adjust if deployed elsewhere
USER = "superuser"

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Chat Assistant", layout="wide")
st.title("💬 Chat Assistant")

with st.sidebar:
    st.header("Configuration")
    fleet_id = st.selectbox("Select Fleet ID", options=["1", "2"])

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"type": "system", "content": "You are a helpful assistant."}
    ]

# --- Helper functions ---
def append_message(role, content):
    st.session_state.messages.append({"type": role, "content": content})

def make_api_call(endpoint, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    res = requests.post(f"{BASE_URL}/{endpoint}", json=body, headers=headers)
    if not res.ok:
        raise Exception(res.text)
    return res.json()

# --- Chat input ---
query = st.chat_input("Type your message here...")
if query:
    append_message("human", query)

    try:
        with st.spinner("Thinking..."):
            # JWT token generation
            token_response = make_api_call("auth/generate_jwt_token", {
                "sub": USER,
                "fleet_id": fleet_id,
                "exp_hours": 1
            })
            token = token_response["token"]

            # API call to chat
            chat_response = make_api_call("chat/execute_user_query", {
                "messages": st.session_state.messages,
                "query": query  # Required by backend, though unused
            }, token)

            assistant_reply = chat_response["response"]
            append_message("ai", assistant_reply)

    except Exception as e:
        st.error(str(e))

# --- Display conversation ---
for message in st.session_state.messages:
    if message["type"] == "human":
        with st.chat_message("user"):
            st.markdown(message["content"])
    elif message["type"] == "ai":
        with st.chat_message("assistant"):
            st.markdown(message["content"])
    elif message["type"] == "system":
        with st.chat_message("system"):
            st.markdown(f"_System: {message['content']}_")
