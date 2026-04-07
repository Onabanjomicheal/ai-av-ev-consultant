"""
Minimal JWT auth.
For a portfolio project this is intentionally lightweight.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from pydantic_settings import BaseSettings

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class AuthSettings(BaseSettings):
    secret_key: str = ""
    algorithm: str = "HS256"
    token_expire_minutes: int = 60 * 24  # 24h
    env: str = "dev"

    class Config:
        env_file = ".env"
        extra = "ignore"


class TokenRequest(BaseModel):
    username: str
    password: str


def _get_jwt():
    try:
        from jose import JWTError, jwt
        return JWTError, jwt
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Auth dependencies missing: {e}. Install requirements.txt.",
        )


def create_token(data: dict) -> str:
    JWTError, jwt = _get_jwt()
    s = AuthSettings()
    if not s.secret_key and s.env.lower() != "dev":
        raise HTTPException(status_code=500, detail="Auth misconfigured: SECRET_KEY missing")
    secret = s.secret_key or "dev_secret_change_in_production"
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=s.token_expire_minutes)
    return jwt.encode(payload, secret, algorithm=s.algorithm)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    JWTError, jwt = _get_jwt()
    s = AuthSettings()
    if not s.secret_key and s.env.lower() != "dev":
        raise HTTPException(status_code=500, detail="Auth misconfigured: SECRET_KEY missing")
    secret = s.secret_key or "dev_secret_change_in_production"
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return jwt.decode(credentials.credentials, secret, algorithms=[s.algorithm])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/token")
async def get_token(req: TokenRequest):
    # Demo: accept any non-empty credentials (replace with DB lookup for production)
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    token = create_token({"sub": req.username})
    return {"access_token": token, "token_type": "bearer"}
