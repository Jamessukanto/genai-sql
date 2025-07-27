import os
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from core.llm_agent.nodes import (
    ListTablesNode,
    CallGetSchemaNode,
    GenerateQueryNode,
    CheckQueryNode,
    should_continue,
)
from core.llm_agent.utils import handle_empty_results, get_model_config, MODELS
from sqlalchemy import text


async def build_agent(db, llm) -> StateGraph:
    """
    Build an SQL agent with langgraph.
    Nodes flow summary:
    1. List Tables (No LLM involved)
          Agent lists all tables in the database using the list_tables node. 
          This step simply queries the database and does not involve the LLM.
    2. Call Get Schema 
          LLM decides which table schemas are relevant.
          Force LLM output to be schemas tool call.
    3. Get Schema (No LLM involved)
          Simply executes schemas tool, outputs schemas tool message
    4. Generate Query
          LLM takes in schemas tool message. It either:
          - Generates final NL answer (no tool call), ending the process, or
          - Generates sql_db_query tool call, to be checked.
    5. Check Query 
          LLM revises query.
          Force LLM output to be sql_db_query tool call.
    6. Run Query 
          Simply executes run_query tool, outputs run_query tool message.
          Loop back to generate_query node.
    """

    # Initialize sql prebuilt_tools
    prebuilt_tools = SQLDatabaseToolkit(db=db, llm=llm).get_tools()
    list_tables_tool = next(t for t in prebuilt_tools if t.name == "sql_db_list_tables")
    get_schema_tool = next(t for t in prebuilt_tools if t.name == "sql_db_schema")
    run_query_tool = next(t for t in prebuilt_tools if t.name == "sql_db_query")

    # Patch to gracefully handle empty results 
    original_run = run_query_tool._run
    run_query_tool._run = handle_empty_results(original_run)


    # Use fast LLM for NL answer generation
    fast_model_config = get_model_config(MODELS["fast"])
    fast_llm = ChatGroq(
        model=fast_model_config["model"],
        temperature=fast_model_config["temperature"],
        max_tokens=fast_model_config["max_tokens"],
        api_key=os.getenv("GROQ_API_KEY")
    )

    # Build state graph
    builder = StateGraph(MessagesState)  #TODO: Human in loop
    builder.add_node("list_tables", ListTablesNode(list_tables_tool))
    builder.add_node("call_get_schema", CallGetSchemaNode(llm, get_schema_tool))
    builder.add_node("get_schema", ToolNode([get_schema_tool], name="get_schema"))
#     builder.add_node("generate_query", GenerateQueryNode(db, llm, run_query_tool))
    builder.add_node("generate_query", GenerateQueryNode(db, llm, fast_llm, run_query_tool))
    builder.add_node("check_query", CheckQueryNode(db, llm, run_query_tool))
    builder.add_node("run_query", ToolNode([run_query_tool], name="run_query"))

    builder.add_edge(START, "list_tables")
    builder.add_edge("list_tables", "call_get_schema")
    builder.add_edge("call_get_schema", "get_schema")
    builder.add_edge("get_schema", "generate_query")
    builder.add_conditional_edges("generate_query", should_continue)
    builder.add_edge("check_query", "run_query")
    
    # Add conditional edge from run_query to either END or generate_query
    def should_continue_after_query(state: MessagesState):
        """After running a query, check if we should continue or end."""
        last_message = state["messages"][-1]
        # Check if the last message is a tool result (indicating we need to generate final answer)
        is_tool_result = (
            hasattr(last_message, 'content') and 
            last_message.content and 
            isinstance(last_message.content, str) and
            ('[' in last_message.content and ']' in last_message.content)  # Tool result format
        )
        
        if is_tool_result:
            # Continue to generate_query to create natural language response
            return "generate_query"
        else:
            # It's already a natural language response, end
            return END
    
    builder.add_conditional_edges("run_query", should_continue_after_query)

    agent = builder.compile()
    return agent


