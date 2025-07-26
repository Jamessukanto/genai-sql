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
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌────────────┐
│  Streamlit  │     │   FastAPI   │     │  LangChain   │     │ PostgreSQL │
│  Frontend   ├─────┤   Backend   ├─────┤  LLM Agent   ├─────┤    DB      │
└─────────────┘     └─────────────┘     └──────────────┘     └────────────┘
                            │                                        │
                            │            Row-Level Security          │
                            └────────────────────────────────────────┘
```

## 📁 Project Structure

```
.
├── Makefile                    
├── docker-compose.yml    
│   
├── backend/                   
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── core/
│   │   ├── db_con.py              # Database connection 
│   │   ├── llm_agent/             # LLM agent & semantic mapping
│   │   ├── setup-ssl-certs.sh  
│   │   └── setup_database/     
│   │       ├── setup_database.py  # Sets up tables + roles with RLS
│   │       └── import_data.py     # Seed database
│   ├── data/                      # Data samples
│   ├── setup_render.py            # Render-specific server setup 
│   ├── routes/                
│   │   ├── auth/                  # JWT auth endpoint
│   │   └── chat/                  # LLM chat endpoint
│   ├── tests/                  
│   └── main.py                    # FastAPI app
│  
└── frontend/                  
    ├── Dockerfile
    ├── requirements.txt                   
    └── main.py                    # Streamlit app
```


## 🌐 Live Demo

**Try it out online!** 🚀

| Service | URL |
|---------|-----|
| **Frontend** | [https://genai-sql-2-frontend.onrender.com/](https://genai-sql-2-frontend.onrender.com/) |
| **Backend API** | [https://genai-sql-2.onrender.com/](https://genai-sql-2.onrender.com/) |
| **API Doc** | [https://genai-sql-2.onrender.com/redoc](https://genai-sql-2.onrender.com/redoc) |

> ⚠️ **Note:** Free-tier LLM calls are limited.

<br>

## 🚀 Quick Start

### 1. Clone the repository:
   ```bash
   git clone https://github.com/Jamessukanto/genai-sql.git
   cd genai-sql
   ```

### 2. Development:

   Requirements:
   - docker
   - docker compose (not docker-compose)


   ```bash
   # Get your API key at https://groq.com/
   export GROQ_API_KEY="get_your_api_key"
   ```
   <br>

   Start FastAPI backend, frontend, and PostgreSQL services: 
   ```bash
   # This seeds sample data, too!
   make dev
   ```
   [http://localhost:8501/](http://localhost:8501/)
   
   <br>


   <details>
   <summary><strong>Debug</strong></summary>

   ```bash
   # View logs
   docker compose logs frontend
   docker compose logs backend
   docker compose logs db
   ```

   </details>




### 3. Test:
   ```bash
   make test
   ```

### 4. Clean up
   ```bash
   # This remove volumes, too
   make clean
   ```





## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.













