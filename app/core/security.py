from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials) -> bool:
    # Implementa tu lógica de autenticación aquí
    # Por ahora, aceptamos cualquier token para desarrollo
    return True