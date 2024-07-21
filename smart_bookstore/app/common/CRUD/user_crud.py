from sqlalchemy.orm import Session
from app.common.database.models import User
from app.schemas.user import UserSchema
from app.middleware.auth import get_password_hash, verify_password

def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserSchema) -> User:
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise ValueError("Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        password_hash=hashed_password,
        role="user"  #  default role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
