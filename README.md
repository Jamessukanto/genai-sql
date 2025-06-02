# EV Fleet Analytics AI Assistant

A natural language interface for querying electric vehicle fleet telemetry data. 

## 🌟 Features

- Natural language to SQL conversion for fleet analytics
- LangGraph-based LLM agent with 'mistral-medium-latest'
- PostgreSQL with row-level security, ensuring fleets only access their own data
- Real-time telemetry analysis (SOC, temperature, usage patterns)
- JWT-based authentication
- Simple Web UI

## 🏗 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   FastAPI   │     │  LangChain   │     │ PostgreSQL │
│   Backend   ├─────┤  LLM Agent   ├─────┤    DB      │
└─────────────┘     └──────────────┘     └────────────┘
       │                                        │
       │            Row-Level Security          │
       └────────────────────────────────────────┘
```

## 📁 Project Structure

```
api/
├── app/
│   ├── llm/                  # LLM agent and semantic mapping
│   ├── services/             # Backend services
│   │   ├── auth_service/     # Authentication and JWT handling
│   │   ├── chat_service/     # LLM chat interface and configs
│   │   ├── sql_service/      # Database operations
│   │   └── service_utils.py
│   └── main.py               # FastAPI app
├── data/                     # Sample data
├── frontend/           
├── scripts/                  
│   ├── setup_data/           # Database init scripts
│   │   ├── import_data.py    # CSV data import with RLS
│   │   ├── setup_database.py # Schema and table creation
│   │   ├── setup_user.py     # User permissions and roles
│   │   └── table_queries.py  # Tables creation queries
│   └── init-certs.sh         # Generate ssl certs
├── tests/             
├── Dockerfile         
├── db.py                     # Database connection and config
└── requirements.txt   
```

## 🚀 Quick Start

### 1. Clone the repository:
   ```bash
   git clone https://github.com/Jamessukanto/genai-sql.git
   cd genai-sql
   ```

### 2. Development:
   ```bash
   # Get your Mistral API key 
   export MISTRAL_API_KEY="your_mistral_api_key"
   ```
   <br>

   Start FastAPI backend, frontend, and PostgreSQL services (This seeds sample data, too!)   
   ```bash
   make dev
   ```
   <br>

   Verify Row-Level Security (RLS) manually
   ```bash
   docker-compose exec db psql -U end_user -d fleetdb; 

   # Simulate RLS by setting the fleet ID context
   SET app.fleet_id = '1';

   # Expected return: Only rows where fleet_id = '1' (3 rows)
   SELECT * FROM vehicles;
   ```

   #### Generate JWT token 
   ```bash
   export ROLE="end_user"
   export FLEET_ID="1"  # Available IDs are "1" and "2"
   ```
   ```bash
   TOKEN=$( \
      curl -s -X POST "$API_URL/auth/generate_jwt_token" \
        -H "$CONTENT_HEADER" \
        -d "{\"sub\": \"$ROLE\", \"fleet_id\": \"$FLEET_ID\", \"exp_hours\": 1}" \
    | sed -n 's/.*"token":"\([^"]*\)".*/\1/p' )
   ```

   #### Execute user query
   ```bash
   curl -X POST "$API_URL/chat/execute_user_query" \
      -H "$CONTENT_HEADER" -H "Authorization: Bearer $TOKEN" \
      -d '{
            "query": "How many SRM T3 EVs are in my fleet?",
            "messages": [{
               "role": "user",
               "content": "How many SRM T3 EVs are in my fleet?"
            }]
         }'
   ```

   Or, go to http://localhost:8501/ and submit your prompt. For the same query as above, the response should return:
   - If fleet_id = "1" → answer is '2 EVs'
   - If fleet_id = "2" → answer is 'No Evs'

   <br>
   <br>

### 3. Test:
   ```bash
   make test
   ```

### 4. Clean up
   ```bash
   # This remove volumes, too
   make clean
   ```

## 🌐 Demo

Live demo: https://genai-sql-1.onrender.com/app <br> (Note that the demo is **temporary**, and Mistral API calls are **not free**.)

Health check endpoint: https://genai-sql-1.onrender.com/api/ping

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
