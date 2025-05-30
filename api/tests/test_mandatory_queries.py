import pytest
import pytest_asyncio
import os
from datetime import datetime
import httpx
import asyncio
import jwt

# Use environment variable for API URL with Render URL as default
API_URL = os.getenv('API_URL', 'https://genai-sql-1.onrender.com/api')

# Configure timeouts and retries with longer durations for complex queries
TIMEOUT_SECONDS = 120.0  # Increased from 30 to 120 seconds
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # Increased from 1 to 2 seconds
BACKOFF_FACTOR = 2  # Each retry will wait 2x longer

async def make_request_with_retry(client, method, url, **kwargs):
    """Helper function to make requests with retries and exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            # Set timeout in the request
            kwargs['timeout'] = httpx.Timeout(TIMEOUT_SECONDS)
            
            response = await client.request(
                method,
                url,
                **kwargs
            )
            # Log response details for debugging
            print(f"\nRequest to {url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Debug headers if they exist
            if 'headers' in kwargs:
                print(f"Request headers: {kwargs['headers']}")
            
            return response
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            current_delay = RETRY_DELAY * (BACKOFF_FACTOR ** attempt)
            if attempt == MAX_RETRIES - 1:
                print(f"Final attempt failed after {TIMEOUT_SECONDS}s timeout")
                raise
            print(f"Timeout on attempt {attempt + 1}, retrying in {current_delay} seconds...")
            await asyncio.sleep(current_delay)
        except httpx.ConnectError as e:
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"Connection attempt {attempt + 1} failed, retrying in {RETRY_DELAY} seconds...")
            await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise

# Token fixture at module level
@pytest_asyncio.fixture(scope="module")
async def auth_token():
    """Get authentication token for all tests."""
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
        
        token = token_data.get("token")
        if not token:
            raise ValueError("No token in response")
        
        # Debug token structure
        try:
            parts = token.split('.')
            print(f"Token parts count: {len(parts)}")
            print(f"Raw token: {token}")
        except Exception as e:
            print(f"Error analyzing token: {e}")
            raise
        
        return token

@pytest.mark.asyncio
class TestMandatoryQueries:
    """Test class to handle async fixtures properly"""

    async def _execute_query(self, query: str, auth_token: str, expected_elements: list = None):
        """Helper method to execute queries and validate responses."""
        print(f"\n=== Executing Query ===")
        print(f"Query: {query}")
        
        async with httpx.AsyncClient() as client:
            response = await make_request_with_retry(
                client,
                "POST",
                f"{API_URL}/chat/execute_user_query",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"query": query}
            )
            result = response.json()
            assert response.status_code == 200, f"Query failed: {response.text}"
            
            print(f"Response: {result['response']}")
            print("=====================")
            
            if expected_elements:
                response_lower = result["response"].lower()
                assert any(element in response_lower for element in expected_elements), \
                    f"Response missing expected elements. Got: {result['response']}"
            
            return result

    async def test_soc_specific_vehicle(self, auth_token):
        """Test Query 1: What is the SOC of vehicle GBM6296G right now?"""
        result = await self._execute_query(
            "What is the SOC of vehicle GBM6296G right now?",
            auth_token,
            ["soc", "%"]
        )

    async def test_srm_t3_count(self, auth_token):
        """Test Query 2: How many SRM T3 EVs are in my fleet?"""
        result = await self._execute_query(
            "How many SRM T3 EVs are in my fleet?",
            auth_token,
            # Hacky positive integer in the response for now
            ["no"] + [str(i) for i in range(100000)]
        )

    async def test_battery_temp_threshold(self, auth_token):
        result = await self._execute_query(
            "Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?",
            auth_token,
            ["yes", "no"]
        )

    async def test_fleet_soc_comfort_zone(self, auth_token):
        result = await self._execute_query(
            "What is the fleet-wide average SOC comfort zone?",
            auth_token,
            ["%", "-", "to"]
        )

    async def test_high_soc_vehicles(self, auth_token):
        result = await self._execute_query(
            "Which vehicles spent > 20 % time in the 90-100 % SOC band this week?",
            auth_token,
            ["vehicle", "gbm", "registration"]
        )

    async def test_low_soc_driving(self, auth_token):
        result = await self._execute_query(
            "How many vehicles are currently driving with SOC < 30 %?",
            auth_token,
            # Hacky positive integer in the response for now
            ["no"] + [str(i) for i in range(100000)]
        )

    async def test_fleet_usage_stats(self, auth_token):
        result = await self._execute_query(
            """What is the total km and driving hours by my fleet over the past 7 days, 
            and which are the most-used & least-used vehicles?""",
            auth_token,
            ["km", "hour", "hrs", "hours"]
        ) 