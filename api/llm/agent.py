#TODO: Human in loop


import os
from typing import Literal

from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from llm.llm_utils import init_tools
from llm.nodes import (
    list_tables, call_get_schema, generate_query,
    check_query, should_continue,
)


# Set up database and LLM
db = SQLDatabase.from_uri(os.getenv("DATABASE_URL"))
llm = init_chat_model(model="mistral-medium-latest", temperature=0)

# Initialize community-built tools
list_tables_tool, get_schema_tool, run_query_tool = init_tools(db, llm)

# Build state graph
builder = StateGraph(MessagesState)
builder.add_node(list_tables)
builder.add_node(call_get_schema)
builder.add_node(ToolNode([get_schema_tool], name="get_schema"), "get_schema")
builder.add_node(generate_query)
builder.add_node(check_query)
builder.add_node(ToolNode([run_query_tool], name="run_query"), "run_query")

builder.add_edge(START, "list_tables")
builder.add_edge("list_tables", "call_get_schema")
builder.add_edge("call_get_schema", "get_schema")
builder.add_edge("get_schema", "generate_query")
builder.add_conditional_edges("generate_query", should_continue)
builder.add_edge("check_query", "run_query")
builder.add_edge("run_query", "generate_query")

# Nodes flow summary:
# 1. List Tables (No LLM involved)
#       Agent lists all tables in the database using the list_tables node. 
#       This step simply queries the database and does not involve the LLM.
# 2. Call Get Schema 
#       LLM decides which table schemas are relevant.
#       Force LLM output to be schemas tool call.
# 3. Get Schema (No LLM involved)
#       Simply executes schemas tool, outputs schemas tool message
# 4. Generate Query
#       LLM takes in schemas tool message. It either:
#       - Generates final NL answer (no tool call), ending the process, or
#       - Generates sql_db_query tool call, to be checked.
# 5. Check Query 
#       LLM revises query.
#       Force LLM output to be sql_db_query tool call.
# 6. Run Query 
#       Simply executes run_query tool, outputs run_query tool message.
#       Loop back to generate_query node.

# Compile into an agent
agent = builder.compile()




