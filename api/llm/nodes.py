import uuid
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, END
from langchain_community.utilities import SQLDatabase

from llm.prompts import generate_query_prompt, check_query_prompt
from llm.llm_utils import load_semantic_map


class ListTablesNode:
    def __init__(self, list_tables_tool):
        self.list_tables_tool = list_tables_tool

    def __call__(self, state: MessagesState):
        tool_call = {
            "name": "sql_db_list_tables",
            "args": {},
            "id": str(uuid.uuid4()),
            "type": "tool_call",
        }
        tool_call_message = AIMessage(content="", tool_calls=[tool_call])
        tool_message = self.list_tables_tool.invoke(tool_call)
        return {"messages": [tool_call_message, tool_message]}

class CallGetSchemaNode:
    def __init__(self, llm, get_schema_tool):
        self.llm = llm
        self.get_schema_tool = get_schema_tool

    def __call__(self, state: MessagesState):
        llm_with_tools = self.llm.bind_tools([self.get_schema_tool], tool_choice="any")
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

class GenerateQueryNode:
    def __init__(self, db: SQLDatabase, llm, run_query_tool):
        self.db = db
        self.llm = llm
        self.run_query_tool = run_query_tool

    def __call__(self, state: MessagesState):
        system_message = {
            "role": "system",
            "content": generate_query_prompt(
                dialect=self.db.dialect,
                row_limit=5000,
                time_limit_sec=10,
                mappings=load_semantic_map()
            ),
        }
        llm_with_tools = self.llm.bind_tools([self.run_query_tool])
        response = llm_with_tools.invoke([system_message] + state["messages"])
        return {"messages": [response]}

class CheckQueryNode:
    def __init__(self, db: SQLDatabase, llm, run_query_tool):
        self.db = db
        self.llm = llm
        self.run_query_tool = run_query_tool

    def __call__(self, state: MessagesState):
        system_message = {
            "role": "system",
            "content": check_query_prompt(dialect=self.db.dialect),
        }
        tool_call = state["messages"][-1].tool_calls[0]
        user_message = {"role": "user", "content": tool_call["args"]["query"]}
        llm_with_tools = self.llm.bind_tools([self.run_query_tool], tool_choice="any")
        response = llm_with_tools.invoke([system_message, user_message])
        response.id = state["messages"][-1].id
        return {"messages": [response]}

# class ShouldContinueNode:
#     def __call__(self, state: MessagesState):
#         last_message = state["messages"][-1]
#         return "check_query" if last_message.tool_calls else END
    

# def list_tables(state: MessagesState):
#     tool_call = {
#         "name": "sql_db_list_tables",
#         "args": {},
#         "id": str(uuid.uuid4()),
#         "type": "tool_call",
#     }
#     tool_call_message = AIMessage(content="", tool_calls=[tool_call])
#     tool_message = list_tables_tool.invoke(tool_call)
#     return {"messages": [tool_call_message, tool_message]}


# def call_get_schema(state: MessagesState):
#     llm_with_tools = llm.bind_tools([get_schema_tool], tool_choice="any")
#     response = llm_with_tools.invoke(state["messages"])
#     return {"messages": [response]}


# def generate_query(state: MessagesState):
#     system_message = {
#         "role": "system",
#         "content": generate_query_prompt(
#             dialect=db.dialect,
#             row_limit=5000,
#             time_limit_sec=10,
#             mappings=load_semantic_map()
#         ),
#     }
#     llm_with_tools = llm.bind_tools([run_query_tool])
#     response = llm_with_tools.invoke([system_message] + state["messages"])
#     return {"messages": [response]}


# def check_query(state: MessagesState):
#     system_message = {
#         "role": "system",
#         "content": check_query_prompt(dialect=db.dialect),
#     }
#     tool_call = state["messages"][-1].tool_calls[0]
#     user_message = {"role": "user", "content": tool_call["args"]["query"]}
#     llm_with_tools = llm.bind_tools([run_query_tool], tool_choice="any")
#     response = llm_with_tools.invoke([system_message, user_message])
#     response.id = state["messages"][-1].id
#     return {"messages": [response]}


def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    return "check_query" if last_message.tool_calls else END

