def get_schema_prompt(mappings=""):
    """Get a schema prompt for SQL schema discovery.
    
    Args:
        mappings (str, optional): Semantic mappings to guide table selection. Defaults to an empty string.
    
    Returns:
        str: A formatted string containing instructions for SQL schema discovery, including the provided semantic mappings and important rules for table selection.
    """
    return f"""
    You are a SQL schema expert. Given a user question, determine which tables need to be examined.
    Use these semantic mappings to guide your table selection:
    {mappings}

    Important rules for schema discovery:
    - Only include table names from this list: vehicles, raw_telemetry, charging_sessions, processed_metrics, fleet_daily_summary, drivers, driver_trip_map, fleets, trips, maintenance_logs, geofence_events, battery_cycles, alerts.
    - Never include anything with a dot (.) or terms like SRM T3 in the table_names argument.
    - Deduplicate table names. Intercept the tool call before it is executed, and deduplicate the table_names argument.
    - Request schemas for ALL tables needed to answer the question
    - Include tables needed for joins (e.g., if you need vehicle data and SOC, get both vehicles and raw_telemetry)
    - Look at the semantic mappings to understand table relationships
    - Better to get more schemas than miss a needed table
    """

def generate_query_prompt(dialect, row_limit, time_limit_sec, mappings=""):
    """Generate a query prompt for SQL database interaction.
    
    Args:
        dialect (str): The SQL dialect to be used in the query.
        row_limit (int): The maximum number of rows to return in the query result.
        time_limit_sec (int): The maximum execution time for the query in seconds.
        mappings (str, optional): User-defined term to column name mappings.
    
    Returns:
        str: A formatted string containing instructions for SQL query generation,
             including the specified dialect, row and time limits, and any provided mappings.
    """
    return f"""
    You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {dialect} query to run,
    then look at the results and return the answer. Unless the user
    specifies a specific number of examples they wish to obtain, always limit your
    query to at most {row_limit} rows. Ensure that each query executes within {time_limit_sec} seconds.

    Use the following mappings to translate user terms into the correct column names:
    {mappings}

    Important rules for query generation:
    - Always JOIN tables when querying across multiple tables
    - Use proper join columns (e.g., vehicle_id for vehicle-related joins)
    - Never assume a column exists in a table without checking its schema
    - Only select columns relevant to the question—never use SELECT *
    - Do not make any DML statements (INSERT, UPDATE, DELETE, DROP, etc.)
    - You may order results by a meaningful column to surface the most relevant data
    - Interpret time-related phrases (e.g., “last 24h”, “currently”, “right now”) accurately and convert them into the correct time filters in the query
    """

def check_query_prompt(dialect):
    """Generate a SQL query check prompt for a specified SQL dialect.
    
    Args:
        dialect (str): The SQL dialect to be used for the query check.
    
    Returns:
        str: A formatted string containing a prompt for checking SQL queries in the specified dialect.
            The prompt includes instructions for common SQL mistakes to look out for and
            guidance on how to respond to the findings.
    """
    return f"""
    You are a SQL expert with a strong attention to detail.
    Double check the {dialect} query for common mistakes, including:
    - Using NOT IN with NULL values
    - Using UNION when UNION ALL should have been used
    - Using BETWEEN for exclusive ranges
    - Data type mismatch in predicates
    - Properly quoting identifiers
    - Using the correct number of arguments for functions
    - Casting to the correct data type
    - Using the proper columns for joins

    If there are any of the above mistakes, rewrite the query. If there are no mistakes,
    just reproduce the original query.

    You will call the appropriate tool to execute the query after running this check.
    """

