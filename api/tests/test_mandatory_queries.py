import pytest
import os
from datetime import datetime
import httpx
import asyncio

# Use environment variable for API URL with Render URL as default
API_URL = os.getenv('API_URL', 'https://genai-sql-1.onrender.com/api')

# Configure httpx client with appropriate timeouts and retries
TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0

async def make_request_with_retry(client, method, url, **kwargs):
    """Helper function to make requests with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.request(
                method,
                url,
                timeout=TIMEOUT_SECONDS,
                **kwargs
            )
            # Log response details for debugging
            print(f"\nRequest to {url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return response
        except httpx.ConnectError as e:
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"Connection attempt {attempt + 1} failed, retrying in {RETRY_DELAY} seconds...")
            await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise


@pytest.mark.asyncio
class TestMandatoryQueries:
    """Test class to handle async fixtures properly"""
    
    # Class-level token storage
    auth_token = None
    
    @classmethod
    async def get_auth_token(cls):
        """Get authentication token if not already obtained"""
        if cls.auth_token is None:
            async with httpx.AsyncClient() as client:
                auth_data = {
                    "sub": "superuser",
                    "fleet_id": "fleet1",
                    "exp_hours": 1
                }
                response = await make_request_with_retry(
                    client,
                    "POST",
                    f"{API_URL}/auth/generate_jwt_token",
                    json=auth_data
                )
                assert response.status_code == 200, f"Auth failed: {response.text}"
                token_data = response.json()
                print(f"Generated token data: {token_data}")
                cls.auth_token = token_data.get("token")
                if not cls.auth_token:
                    raise ValueError("No token in response")
        return cls.auth_token

    @pytest.fixture(autouse=True)
    async def setup_auth(self):
        """Setup fixture that ensures we have an auth token"""
        await self.get_auth_token()
        
    async def test_soc_specific_vehicle(self):
        """Test Query 1: What is the SOC of vehicle GBM6296G right now?"""
        query = "What is the SOC of vehicle GBM6296G right now?"
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            # Validate response contains SOC percentage
            assert "SOC" in result["response"]
            assert "%" in result["response"]

    async def test_srm_t3_count(self):
        """Test Query 2: How many SRM T3 EVs are in my fleet?"""
        query = "How many SRM T3 EVs are in my fleet?"
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            # Validate response contains a number
            assert any(char.isdigit() for char in result["response"])

    async def test_battery_temp_threshold(self):
        """Test Query 3: Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?"""
        query = "Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?"
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            # Validate response is a yes/no answer
            assert any(word in result["response"].lower() for word in ["yes", "no"])

    async def test_fleet_soc_comfort_zone(self):
        """Test Query 4: What is the fleet-wide average SOC comfort zone?"""
        query = "What is the fleet-wide average SOC comfort zone?"
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            # Validate response contains percentage range
            assert "%" in result["response"]
            assert "-" in result["response"] or "to" in result["response"]

    async def test_high_soc_vehicles(self):
        """Test Query 5: Which vehicles spent > 20 % time in the 90-100 % SOC band this week?"""
        query = "Which vehicles spent > 20 % time in the 90-100 % SOC band this week?"
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            # Validate response contains vehicle identifiers
            assert any(id_type in result["response"].lower() 
                      for id_type in ["vehicle", "gbm", "registration"])

    async def test_low_soc_driving(self):
        """Test Query 6: How many vehicles are currently driving with SOC < 30 %?"""
        query = "How many vehicles are currently driving with SOC < 30 %?"
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            # Validate response contains a number
            assert any(char.isdigit() for char in result["response"])

    async def test_fleet_usage_stats(self):
        """Test Query 7: What is the total km and driving hours by my fleet over the past 7 days, 
        and which are the most-used & least-used vehicles?"""
        query = """What is the total km and driving hours by my fleet over the past 7 days, 
        and which are the most-used & least-used vehicles?"""
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            # Validate response contains distance and time metrics
            assert "km" in result["response"]
            assert any(word in result["response"].lower() 
                      for word in ["hours", "hrs", "hour"]) 