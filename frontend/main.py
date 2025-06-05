import streamlit as st
import requests

# --- Configuration ---
BASE_URL = "http://backend:8000"
USER = "superuser"

# --- Page Setup ---
st.set_page_config(page_title="💬 Chat Assistant", layout="wide", initial_sidebar_state="expanded")

# --- Title ---
st.title("SQL Chat Assistant Demo")

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")
    fleet_id = st.selectbox("Select Fleet ID", options=["1", "2"])
    mistral_api_key = st.text_input("Mistral API Key", type="password")

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Helpers ---
def append_message(role, content):
    """Append a message to the session state messages.
    
    Args:
        role (str): The role of the message sender (e.g., 'user', 'assistant').
        content (str): The content of the message to be appended.
    
    Returns:
        None: This method doesn't return anything, it modifies the session state in-place.
    """
    st.session_state.messages.append({"type": role, "content": content})

def make_api_call(endpoint, body=None, token=None):
    """Makes an API call to a specified endpoint.
    
    Args:
        endpoint (str): The API endpoint to call.
        body (dict, optional): The JSON body to send with the request. Defaults to None.
        token (str, optional): The authentication token. If provided, it will be used in the Authorization header. Defaults to None.
    
    Returns:
        dict: The JSON response from the API.
    
    Raises:
        Exception: If the API request is not successful (non-2xx status code).
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    res = requests.post(f"{BASE_URL}/{endpoint}", json=body, headers=headers)
    if not res.ok:
        raise Exception(res.text)
    return res.json()

# --- Chat Input ---
query = st.chat_input("Type your message here...")
if query:
    append_message("human", query)


    try:
        with st.spinner("Thinking..."):
            token = make_api_call("api/auth/generate_jwt_token", {
                "sub": USER,
                "fleet_id": fleet_id,
                "exp_hours": 1
            })["token"]

            chat_response = make_api_call("api/chat/execute_user_query", {
                "messages": st.session_state.messages,
                "query": query,
                # "mistral_api_key": mistral_api_key   # pass it in request body
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
