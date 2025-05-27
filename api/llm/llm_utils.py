import yaml
from langchain_community.agent_toolkits import SQLDatabaseToolkit

def load_semantic_map():
    with open("config/semantic_map.yaml") as f:
        m = yaml.safe_load(f)

    mappings_str = []
    for term, info in m.items():
        cols = ", ".join(info["columns"])
        mappings_str.append(f"- '{term}'. {info['description']} → [{cols}]")

    return "\n".join(mappings_str)

def init_tools(db, llm):
    tools = SQLDatabaseToolkit(db=db, llm=llm).get_tools()
    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
    run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
    return list_tables_tool, get_schema_tool, run_query_tool
