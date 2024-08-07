from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.common.database.models import User
from app.schemas.user import UserSchema
from app.middleware.auth import get_password_hash, verify_password

def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserSchema) -> User:
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        password_hash=hashed_password,
        role="user"  # default role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return user

def get_users_with_pagination(db: Session, page: int, page_size: int) -> List[User]:
    offset = (page - 1) * page_size
    return db.query(User).limit(page_size).offset(offset).all()

def delete_user(db: Session, username: str) -> User:
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user
