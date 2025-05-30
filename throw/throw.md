# Setup database
curl -X POST https://genai-sql-1.onrender.com/sql/setup

# Import data
curl -X POST https://genai-sql-1.onrender.com/api/sql/import_data -H "Content-Type: application/json" -d '{"csv_dir": "data_throw"}'

# Generate JWT token
curl -X POST https://genai-sql-1.onrender.com/api/auth/generate_jwt_token 
-H "Content-Type: application/json" 
-d '{"sub": "superuser", "fleet_id": "fleet1", "exp_hours": 24}'


# Execute SQL
API_URL="https://genai-sql-1.onrender.com/api" && \
CONTENT_HEADER="Content-Type: application/json" && \

TOKEN=$( \
curl -s -X POST "$API_URL/auth/generate_jwt_token" \
    -H "$CONTENT_HEADER" \
    -d '{"sub": "superuser", "fleet_id": "fleet1", "exp_hours": 1}' \
| sed -n 's/.*"token":"\([^"]*\)".*/\1/p' ) && \

curl -X POST "$API_URL/sql/execute" \
     -H "$CONTENT_HEADER" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"sql": "SELECT * FROM alerts"}'




################################# LOCAL #################################

# Setup database
curl -X POST https://genai-sql-1.onrender.com/api/sql/setup
curl -X POST https://genai-sql-1.onrender.com/api/sql/import_data -H "Content-Type: application/json" -d '{"csv_dir": "/data_throw"}'


# Execute SQL query
API_URL="https://genai-sql-1.onrender.com/api" && \
CONTENT_HEADER="Content-Type: application/json" && \

TOKEN=$( \
curl -s -X POST "$API_URL/auth/generate_jwt_token" \
    -H "$CONTENT_HEADER" \
    -d '{"sub": "superuser", "fleet_id": "fleet1", "exp_hours": 1}' \
| jq -r '.token') && \

curl -X POST "$API_URL/sql/execute" \
     -H "$CONTENT_HEADER" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"sql": "SELECT * FROM alerts"}'











# LOCAL
uvicorn app.main:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/ping

# CREATE DB
psql -h localhost -U postgres -d fleetdb  
CREATE DATABASE fleetdb;

# IMPORT
python -m scripts.import_data.import_data --csv-dir ./data --drop-existing


# CHECK RLS
# psql
SET app.fleet_id = '1'; SELECT * FROM vehicles;
# Curl
python -m scripts.generate_jwt_token --sub end_user --fleet_id 1 --out_token scripts/token.txt && \

curl -X POST http://localhost:8000/sql/execute_sql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat scripts/token.txt)" \
  -d '{"sql":"SELECT COUNT(*) FROM vehicles;"}'



# CHECK CHAT
python -m api.scripts.generate_jwt_token --sub end_user --fleet_id 2 --out_token api/scripts/token.txt && \
curl -X POST http://localhost:8000/chat/execute_user_query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat api/scripts/token.txt)" \
  -d '{"query":"How many SRM T3 EVs are in my fleet?"}'



"How many SRM T3 EVs are in my fleet?"
"What is the SOC of vehicle GBM6296G right now?"
"Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?"
"What is the fleet‐wide average SOC comfort zone?"
"Which vehicles spent > 20 % time in the 90‐100 % SOC band this week?"
"How many vehicles are currently driving with SOC < 30 %?"
"What is the total km and driving hours by my fleet over the past 7 days, and which
are the most-used & least-used vehicles?"




# CONTAINER
docker-compose down && docker-compose up --build -d && \
docker-compose logs --tail=222 api

# Import data
docker-compose run --rm api python import_data.py --init
docker-compose run --rm api python import_data.py --load-all


# Access psql
docker-compose exec db psql -U postgres -d fleetdb
















# Background
We operate an electric-vehicle analytics platform that ingests high-frequency telemetry
(every 10 seconds) from fleet vans, buses, and trucks worldwide. Operators currently
rely on dashboards and SQL consoles to answer everyday questions such as:
● “Which vans spent more than 20% of the past week above 90% SOC?”
● “Did any vehicle in Depot A cross 33°C battery temperature yesterday?”
The objective of this assignment is to build an AI Chatbot Assistant to support
natural-language Q&A powered by large-language models. Your assignment is to build
a functional MVP of this assistant that:
1. Converts plain-English queries into secure, efficient SQL against the supplied
fleet dataset.
2. Returns concise, human-readable answers (text and/or tables).
3. Enforces row-level security so each fleet sees only its own data.

The following sections describe the schema, evaluation criteria, and submission
guidelines. The sample CSV pack lets you populate a local PostgreSQL database to
test your project.

# Deliverable Notes
1 Running demo hosted on Render (or Fly.io / Railway). Public URL + health endpoint (/ping)
2 GitHub repo MIT or Apache‐2 licence, commit history visible
3 README.md. < 5 min setup (Docker or make dev), architecture diagram, design decisions, how to run tests
4 Sample‐data loading script. Use the CSV pack we provide (see section 3.1) to seed your local PostgreSQL instance
5 Prompt & semantic mapping. YAML/JSON file that maps each user term to a table.column
6 Automated tests Unit + integration (≥ 10 key natural language (NL) queries from section 8)

# Technical Requirements
1. Language & stack: Python 3.10+, FastAPI (or Flask) backend. LangChain OR custom prompt logic allowed.
2. LLM provider: OpenAI, Anthropic, or Mistral. Use function‐calling / tool‐use
paradigm.
3. Database: PostgreSQL 15. Use the CSVs for seeding. Tip: Render’s free PostgreSQL tier is acceptable for this exercise.
4. Vector store (optional): pgvector or equivalent.

# Evaluation Criteria
Weightage Area
30% Correctness of NL → SQL translation & answer formatting
25% Code quality, modularity, and documentation
15% Data modelling & performance (indexes, partitions)
10% Security (RBAC, SQL‐injection guards)
10% Deployment reliability (cold‐start < 30 s, healthcheck)
10% Thoughtfulness of prompts & semantic layer


Term; What it means; Why it matters in the data; 
SOH (State of Health); Snapshot of the battery’s long-term condition: the percentage of its original usable capacity that remains. 100% when new, trending downward as the battery ages and degrades.;; 
SOC (State of Charge); Battery "fuel-gauge" expressed as a percentage (0 % = empty, 100 % = full).; Most queries revolve around SOC thresholds (e.g., "vehicles < 30 %").
SOC comfort zone; The SOC band a fleet considers "healthy" for daily ops—typically 30–80%. Operating outside this band too often accelerates battery ageing.; In the dataset, you’ll see derived metrics such as the average SOC comfort zone and the boolean overcharging flag (time spent > 90 % SOC).
SRM T3; A light-duty electric van: SRM is the make (manufacturer), T3 is the model. Comparable to "Hyundai Ioniq" → make Hyundai, model Ioniq.; Table vehicles.model = 'SRM T3' is frequently filtered in the sample queries.
GBM6296G; A Singapore vehicle registration plate (license-plate number). Plate numbers uniquely identify vehicles in human-facing questions, while vin and vehicle_id do so in the database. VIN Vehicle Identification Number—17-char unique ID issued by OEM.; Used as a secondary key and for cross-referencing external systems.
Trip; A continuous vehicle movement episode from start_ts to end_ts (table trips). Contains distance, energy, idle minutes.;;
Charging session; Period when the vehicle is plugged in (table charging_sessions). Contains start/end SOC and energy delivered. Alert Event that breaches a safety or performance threshold (e.g. HighTemp, Overcharge, LowSOC). Logged in table alerts.;;
Battery cycle; One charging-and-discharging cycle tracked for long-term State-of-Health (SOH) analysis.
Geofence event; Entry/exit of a predefined geographic area (e.g. Depot, Airport).;;
Fleet / Vehicle / Driver hierarchy; fleets → vehicles → trips / alerts / telemetry, and drivers link to trips through driver_trip_map. All natural language (NL) queries should respect this hierarchy.;;