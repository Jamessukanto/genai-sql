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
   # Set your mistral api
   export MISTRAL_API_KEY=your_mistral_api_key

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
   #### Localhost check for RLS <br>
   Go to http://localhost:8000/app/ and submit a prompt like: "How many SRM T3 EVs are in my fleet?" <br>
   The answer should return
   → '2' if fleet_id=1
   → '0' if fleet_id=2
   <br>
   <br>

   ```bash

   # Clean up (This remove volumes, too)
   make clean
   ```

### 3. Testing:
   ```bash
   # Run tests against local environment
   make test-local

   # Run tests against production
   make test
   ```

## 📝 API Examples

1. Generate JWT Token:
```bash
curl -X POST http://localhost:8000/api/auth/generate_jwt_token \
     -H "Content-Type: application/json" \
     -d '{"sub": "superuser", "fleet_id": "fleet1", "exp_hours": 1}'
```

2. Execute Natural Language Query:
```bash
curl -X POST http://localhost:8000/api/chat/execute_user_query \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"query": "How many vehicles are currently driving with SOC below 30%?"}'
```

## 🔒 Security Features

- Row-level security (RLS) enforced at database level
- JWT-based authentication
- Fleet-specific data isolation
- SQL injection prevention through LLM query generation

## 🌐 Demo

Access the live demo at: https://genai-sql-1.onrender.com/app

Health check endpoint: https://genai-sql-1.onrender.com/api/ping

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.