# auth.py

from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader

api_key = APIKeyHeader(name="x-api-key")

async def handle_api_key(key: str = Security(api_key)):
    # No active API key found
    
    if key != "test":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key"
        )

    yield api_key
