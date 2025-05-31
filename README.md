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
│   ├── llm/          # LLM agent and semantic mapping
│   ├── services/     # Auth, SQL, and chat services
│   └── main.py       # FastAPI application
│   └── ssl/
│       └── setup-certs.sh
├── data/         
├── frontend/         
├── scripts/         
│   └── setup_data/   # Database setup and data import
├── tests/            # Tests and pytest config
│   └── pytest.ini
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
   # Set env vars
   export MISTRAL_API_KEY="your_mistral_api_key"
   export API_URL="http://localhost:8000/api"
   export CONTENT_HEADER="Content-Type: application/json"

   # Start FastAPI and PostgreSQL services (This seeds sample data, too!)
   make dev
   ```

   Verify Row-Level Security (RLS) manually
   ```bash
   docker-compose exec db psql -U end_user -d fleetdb; 

   # Simulate RLS by setting the fleet ID context
   SET app.fleet_id = '1';

   # Expected return: Only rows where fleet_id = '1' (3 rows)
   SELECT * FROM vehicles;

   \q
   ```

   #### Generate JWT token 
   ```bash
   # Clean up (This remove volumes, too)
   export USER="superuser"
   export FLEET_ID="1"  # Available IDs are "1" and "2"

    TOKEN=$( \
    curl -s -X POST "$API_URL/auth/generate_jwt_token" \
        -H "$CONTENT_HEADER" \
        -d "{\"sub\": \"$USER\", \"fleet_id\": \"$FLEET_ID\", \"exp_hours\": 1}" \
    | sed -n 's/.*"token":"\([^"]*\)".*/\1/p' )
   ```

   #### Execute user query
   ```bash
    curl -X POST "$API_URL/chat/execute_user_query" \
        -H "$CONTENT_HEADER" -H "Authorization: Bearer $TOKEN" \
        -d '{"query":"How many SRM T3 EVs are in my fleet?"}'
   ```

   Or, go to http://localhost:8000/app/ and submit your prompt. For the same query as above, the answer should return:
   → '2' if fleet_id=1
   → '0' if fleet_id=2
   <br>
   <br>


   ```bash
   # Clean up (This remove volumes, too)
   make clean
   ```

### 3. Test:
   ```bash
   make test
   ```


## 🌐 Demo

Live demo (temporary): https://genai-sql-1.onrender.com/app

Health check endpoint: https://genai-sql-1.onrender.com/api/ping

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.