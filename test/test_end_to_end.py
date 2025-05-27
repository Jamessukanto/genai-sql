import pytest
import subprocess
import requests

@pytest.fixture(scope="module", autouse=True)
def start_services():
    subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
    yield
    subprocess.run(["docker-compose", "down"], check=True)

def test_mandatory_queries():
    url = 'http://localhost:8000/chat'
    headers = {'Content-Type': 'application/json'}
    queries = [
        # "How many SRM T3 EVs are in my fleet?",
        # "What is the SOC of vehicle GBM6296G right now?",
        "Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?",
        # "What is the fleet‐wide average SOC comfort zone?",
        # "Which vehicles spent > 20 % time in the 90‐100 % SOC band this week?",
        # "How many vehicles are currently driving with SOC < 30 %?",
        # "What is the total km and driving hours by my fleet over the past 7 days, and which are the most-used & least-used vehicles?",
    ]
    for q in queries:
        resp = requests.post(url, json={'query': q}, headers=headers)
        assert resp.status_code == 200, f"Failed on: {q}"
        data = resp.json()
        assert 'rows' in data or 'answer' in data

        