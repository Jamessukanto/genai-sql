# EV Fleet Analytics AI Assistant

A natural language interface for querying electric vehicle fleet telemetry data. 

## 🌟 Features

- Natural language to SQL conversion for fleet analytics
- LangGraph-based LLM agent with groq-api, model: 'llama3-70b-8192'
- PostgreSQL with RBAC
- Real-time telemetry analysis (SOC, temperature, usage patterns)
- JWT-based authentication

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
.
├── Makefile
├── docker-compose.yml
├── backend
│   ├── Dockerfile
│   ├── core
│   │   ├── db_con.py           # Set up database connection
│   │   ├── llm_agent           # LLM agent and semantic mapping
│   │   ├── setup-ssl-certs.sh  # ** Set up SSL certs 
│   │   └── setup_data          # Set up tables, roles, RLS and seed data
│   ├── data                    # Sample data
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt
│   ├── routes                  # Endpoints
│   │   ├── auth                # Authentication, JWT handling
│   │   ├── chat                # LLM chat interface and configs
│   │   ├── sql                 # Database ops
│   │   └── utils.py
│   └── tests
└── frontend
    ├── Dockerfile
    ├── main.py
    └── requirements.txt
```

## 🚀 Quick Start

### 1. Clone the repository:
   ```bash
   git clone https://github.com/Jamessukanto/genai-sql.git
   cd genai-sql
   ```

### 2. Development:

   Requirements: docker, docker compose (not docker-compose)

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


   <details>
   <summary><strong>Manually verify Row-Level Security (RLS)</strong></summary>
   
   ```bash
   docker compose exec db psql -U end_user -d fleetdb; 

   # Simulate RLS by setting the fleet ID context
   SET app.fleet_id = '1';

   # Expected return: Only rows where fleet_id = '1' (3 rows)
   SELECT * FROM vehicles;
   ```
   </details>

   <details>
   <summary><strong>Manually execute query</strong></summary>
   
   #### Generate JWT token 
   ```bash
   export ROLE="end_user"
   export FLEET_ID="1"  # Available IDs are "1" and "2"
   export API_URL="http://localhost:8000/api"
   export CONTENT_HEADER="Content-Type: application/json"
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
   </details>

   Or, go to http://localhost:8501/ and submit your prompt. For the same query as above, the response should return:
   - If fleet_id = "1" → answer is '2 EVs'
   - If fleet_id = "2" → answer is 'No Evs'

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

<br>

## 🌐 Demo

Live demo: https://genai-sql-2-frontend.onrender.com <br> (Note that the demo is **temporary**, and Mistral API calls are **not free**.)


## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.



Ideas:
1. Each prompt should be 'self-contained', to reduce window length
2. 

issues tackled:
1. use quality-model for sql generation as it's more tool-use compliant
2. reserve fast-model for consolidation (takes longest)
3. patch run_query_tool to gracefully handle empty results 




What is the SOC of vehicle GBM6296G right now?  
57, no data, 
How many SRM T3 EVs are in my fleet?      
2, 0
Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?      
no data, 
What is the fleet‑wide average SOC comfort zone?”
57.5
Which vehicles spent > 20 % time in the 90‑100 % SOC band this week?
no
How many vehicles are currently driving with SOC < 30 %?
no
What is the total km and driving hours by my fleet over the past 7 days, and which are the most-used & least-used vehicles?