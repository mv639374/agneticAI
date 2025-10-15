# agenticAI/backend/app/mcp/tools/api_caller.py

"""
HTTP API Caller Tool for MCP

This tool allows agents to call external HTTP APIs.

USE CASES:
- Fetch real-time data (weather, stock prices, etc.)
- Integrate with third-party services (Slack, GitHub, etc.)
- Call internal microservices
- Access REST APIs

SECURITY & RATE LIMITING:
- Timeout protection (max 5 minutes)
- Error handling for failed requests
- Logged API calls for audit
- TODO (Phase 3): Add rate limiting per domain
"""

import httpx

from app.mcp.schemas import ApiCallInput, ApiCallOutput, HttpMethod
from app.utils.logger import get_logger

log = get_logger(__name__)


async def call_api(input_data: ApiCallInput) -> ApiCallOutput:
    """
    Call external HTTP API.
    
    Tool Description for LLM:
    "Make HTTP requests to external APIs. Supports GET, POST, PUT, DELETE methods.
    Use this tool when you need to:
    - Fetch data from external services (weather, news, stocks)
    - Call REST APIs
    - Integrate with webhooks
    - Access public or authenticated APIs
    
    Examples:
    - Weather: GET https://api.openweathermap.org/data/2.5/weather?q=London&appid=KEY
    - Create resource: POST https://api.example.com/items with body={'name': 'Item'}
    - Update resource: PUT https://api.example.com/items/123 with body={'status': 'active'}
    
    Authentication:
    - Include API keys in headers: {'Authorization': 'Bearer YOUR_KEY'}
    - Or in URL parameters: https://api.example.com/data?apikey=YOUR_KEY"
    
    Args:
        input_data: API call parameters
    
    Returns:
        ApiCallOutput with response or error
    """
    
    try:
        async with httpx.AsyncClient(timeout=input_data.timeout) as client:
            # Prepare request
            request_kwargs = {
                "method": input_data.method,
                "url": input_data.url,
                "headers": input_data.headers or {},
            }
            
            # Add body for POST/PUT/PATCH
            if input_data.method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
                if input_data.body:
                    request_kwargs["json"] = input_data.body
            
            # Make request
            response = await client.request(**request_kwargs)
            
            # Parse response
            try:
                response_data = response.json()
            except Exception:
                # If not JSON, return text
                response_data = response.text
            
            # Log API call
            log.info(
                "API call completed",
                method=input_data.method,
                url=input_data.url,
                status_code=response.status_code,
                response_size=len(response.text),
            )
            
            return ApiCallOutput(
                success=response.is_success,
                status_code=response.status_code,
                response_data=response_data,
                headers=dict(response.headers),
            )
    
    except httpx.TimeoutException as e:
        log.warning("API call timeout", url=input_data.url, timeout=input_data.timeout)
        return ApiCallOutput(
            success=False,
            error=f"Request timeout after {input_data.timeout} seconds"
        )
    
    except httpx.HTTPError as e:
        log.error("API call failed", url=input_data.url, exc_info=e)
        return ApiCallOutput(
            success=False,
            error=f"HTTP error: {str(e)}"
        )
    
    except Exception as e:
        log.error("API call failed", url=input_data.url, exc_info=e)
        return ApiCallOutput(
            success=False,
            error=f"Request failed: {str(e)}"
        )