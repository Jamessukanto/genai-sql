# EV Fleet Analytics AI Assistant

A natural language interface for querying electric vehicle fleet telemetry data, powered by 'mistral-medium-latest'. 

## 🌟 Features

- Natural language to SQL conversion for fleet analytics
- Row-level security ensuring fleets only access their own data
- Real-time telemetry analysis (SOC, temperature, usage patterns)
- JWT-based authentication
- Web UI

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

Key Components:
- FastAPI backend with authentication and API routing
- LangChain-based LLM agent for natural language processing
- PostgreSQL with row-level security for data isolation
- Simple HTML/CSS frontend for demo purposes

## 📁 Project Structure

```
api/
├── app/
│   ├── llm/          # LLM agent and semantic mapping
│   ├── services/     # Auth, SQL, and chat services
│   └── main.py       # FastAPI application
├── frontend/         
├── scripts/         
│   └── setup_data/   # Database setup and data import
├── tests/            # Integration tests
└── requirements.txt
```

## 🚀 Quick Start

### Using Docker (Recommended)

1. Prerequisites:
   - Docker and Docker Compose installed
   - Sample data files in `./data` directory

2. Start Services:
   ```bash
   # Clone and enter the repository
   git clone <repository-url>
   cd ev-fleet-analytics

   # Start PostgreSQL and API services
   docker-compose up -d
   ```

3. Setup Database:
   ```bash
   # Wait for services to be healthy, then:
   curl -X POST http://localhost:8000/api/sql/setup
   
   # Import sample data
   curl -X POST http://localhost:8000/api/sql/import_data \
        -H "Content-Type: application/json" \
        -d '{"csv_dir": "/app/data"}'
   ```



## 🧪 Testing

Run the test suite:
```bash
cd api
pip install -r tests/requirements-test.txt
python -m pytest tests/test_mandatory_queries.py -v
```

The tests cover:
- Natural language query processing
- Authentication and authorization
- Row-level security
- Data accuracy and consistency

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