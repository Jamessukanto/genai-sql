import uuid
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, END
from langchain_community.utilities import SQLDatabase

from core.llm_agent.prompts import generate_query_prompt, check_query_prompt, get_schema_prompt
from core.llm_agent.utils import load_semantic_map


# from langchain_core.messages import SystemMessage, HumanMessage
# system_message = SystemMessage(content="...")
# user_message = HumanMessage(content=...)


class ListTablesNode:
    def __init__(self, list_tables_tool):
        """Initialize a new instance of the class.
        
        Args:
            list_tables_tool (object): A tool for listing tables, likely used within the class methods.
        
        Returns:
            None: This method doesn't return anything.
        """
        self.list_tables_tool = list_tables_tool

    def __call__(self, state: MessagesState):
        """Executes a tool call to list SQL database tables and updates the message state.
        
        Args:
            self: The instance of the class containing this method.
            state (MessagesState): The current state of messages.
        
        Returns:
            dict: A dictionary containing the updated messages list, which includes the original messages, the tool call message, and the tool response message.
        """
        tool_call = {
            "name": "sql_db_list_tables",
            "args": {},
            "id": str(uuid.uuid4()),
            "type": "tool_call",
        }
        tool_call_message = AIMessage(content="", tool_calls=[tool_call])
        tool_message = self.list_tables_tool.invoke(tool_call)
        # return {"messages": [tool_call_message, tool_message]}
        return {"messages": state["messages"] + [tool_call_message, tool_message]}


class CallGetSchemaNode:
    def __init__(self, llm, get_schema_tool):
        """Initialize a new instance of the class.
        
        Args:
            llm: The language model to be used.
            get_schema_tool: A tool or function to retrieve schema information.
        
        Returns:
            None
        """
        self.llm = llm
        self.get_schema_tool = get_schema_tool

    def __call__(self, state: MessagesState):
        """Handles the invocation of a language model with tools based on the current message state.
        
        Args:
            self: The instance of the class containing this method.
            state (MessagesState): The current state of messages to be processed.
        
        Returns:
            dict: A dictionary containing the updated messages, including the language model's response.
        
        """
        system_message = {
            "role": "system",
            "content": get_schema_prompt(mappings=load_semantic_map())
        }
        llm_with_tools = self.llm.bind_tools([self.get_schema_tool], tool_choice="any")
        response = llm_with_tools.invoke([system_message] + state["messages"])
        # return {"messages": [response]}
        return {"messages": state["messages"] + [response]}

class GenerateQueryNode:
    def __init__(self, db: SQLDatabase, llm, run_query_tool):
        """Initializes a new instance of the class.
        
        Args:
            db (SQLDatabase): The SQL database object to be used for database operations.
            llm: The language model to be used for processing.
            run_query_tool: A tool or function for executing database queries.
        
        Returns:
            None: This method doesn't return anything; it initializes instance attributes.
        """
        self.db = db
        self.llm = llm
        self.run_query_tool = run_query_tool

    def __call__(self, state: MessagesState):
        """Invokes an LLM with tools to process a state of messages.
        
        Args:
            self: The instance of the class containing this method.
            state (MessagesState): The current state of messages to be processed.
        
        Returns:
            dict: A dictionary containing the updated messages, including the LLM's response.
        
        """
        system_message = {
            "role": "system",
            "content": generate_query_prompt(
                dialect=self.db.dialect,
                row_limit=5000,
                time_limit_sec=10,
                mappings=load_semantic_map()
            ),
        }
        print("[AGENT] GenerateQueryNode system_message:", system_message)
        print("[AGENT] GenerateQueryNode state messages:", state["messages"])
        llm_with_tools = self.llm.bind_tools([self.run_query_tool])
        response = llm_with_tools.invoke([system_message] + state["messages"])
        print("[AGENT] GenerateQueryNode LLM response:", response)
        # return {"messages": [response]}
        return {"messages": state["messages"] + [response]}

class CheckQueryNode:
    def __init__(self, db: SQLDatabase, llm, run_query_tool):
        """Initializes a new instance of the class.
        
        Args:
            db (SQLDatabase): The SQL database object to be used for queries.
            llm: The language model to be used for processing.
            run_query_tool: The tool or function used to execute SQL queries.
        
        Returns:
            None: This method doesn't return anything.
        """
        self.db = db
        self.llm = llm
        self.run_query_tool = run_query_tool

    def __call__(self, state: MessagesState):
        """Handles a call to process a query state and generate a response using an LLM with tools.
        
        Args:
            self: The instance of the class containing this method.
            state (MessagesState): The current state of messages in the conversation.
        
        Returns:
            dict: A dictionary containing the updated messages state, including the new response.
        
        """
        system_message = {
            "role": "system",
            "content": check_query_prompt(dialect=self.db.dialect),
        }
        tool_call = state["messages"][-1].tool_calls[0]
        user_message = {"role": "user", "content": tool_call["args"]["query"]}
        print("[AGENT] CheckQueryNode system_message:", system_message)
        print("[AGENT] CheckQueryNode user_message:", user_message)
        llm_with_tools = self.llm.bind_tools([self.run_query_tool], tool_choice="any")
        response = llm_with_tools.invoke([system_message, user_message])
        print("[AGENT] CheckQueryNode LLM response:", response)
        response.id = state["messages"][-1].id
        # return {"messages": [response]}
        return {"messages": state["messages"] + [response]}


# Edges (A router basically)
def should_continue(state: MessagesState):
    """Determines whether to continue processing based on the current state of messages.
    
    Args:
        state (MessagesState): The current state of messages, containing a list of messages.
    
    Returns:
        str: 'check_query' if the last message contains tool calls, otherwise 'END'.
    """
    last_message = state["messages"][-1]
    return "check_query" if last_message.tool_calls else END

