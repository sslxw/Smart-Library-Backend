import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.common.database.database import get_db
from app.common.database.models import User

SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_password_hash(password: str) -> str:
    salt = SECRET_KEY.encode()
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(hashed).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    salt = SECRET_KEY.encode()
    hashed = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt, 100000)
    return hmac.compare_digest(base64.b64encode(hashed).decode(), hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode()
    signature = hmac.new(SECRET_KEY.encode(), encoded_jwt.encode(), hashlib.sha256).digest()
    return f"{encoded_jwt}.{base64.urlsafe_b64encode(signature).decode()}"

def verify_token(token: str):
    try:
        encoded_jwt, signature = token.rsplit('.', 1)
        expected_signature = hmac.new(SECRET_KEY.encode(), encoded_jwt.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(signature.encode(), base64.urlsafe_b64encode(expected_signature)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
                headers={"WWW-Authenticate": "Bearer"}
            )
        payload = json.loads(base64.urlsafe_b64decode(encoded_jwt.encode()).decode())
        if datetime.now(timezone.utc).timestamp() > payload["exp"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return payload
    except (KeyError, ValueError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        ) from e

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"username": user.username, "role": user.role}

def admin_required(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
