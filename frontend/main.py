import streamlit as st
import requests
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    SAMPLE_QUESTIONS,
    append_message,
    truncate_text,
    make_api_call,
    generate_token
)

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


# --- Sidebar with eager token generation ---
with st.sidebar:
    st.header("Configuration")
    fleet_id = st.selectbox("Grant access to fleet:", options=["1", "2"])
    
    # Sample Questions Section
    st.markdown("---")
    st.text("Sample Questions:")
    
    for i, question in enumerate(SAMPLE_QUESTIONS):
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.text(truncate_text(question))
            
            with col2:
                if st.button("→", key=f"send_btn_{i}", help="Send to chat"):
                    st.session_state.pending_question = question
                    st.rerun()


# --- Chat Input ---
query = st.chat_input("Type your message here...")

# Check if there's a pending question from the sidebar and process it immediately
if "pending_question" in st.session_state:
    query = st.session_state.pending_question
    # Clear the pending question immediately to prevent glitches
    del st.session_state.pending_question
    # Process the question right away
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
elif query:  # Only process if it's a new query from chat input
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

