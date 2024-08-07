from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from app.common.database.database import get_db
from app.common.database.models import UserActivity
from app.schemas.user import UserSchema, TokenSchema, UserActivitySchema, ViewUserSchema
from app.middleware.auth import create_access_token, get_current_user, admin_required
from app.common.CRUD.user_crud import (
    get_user_by_username,
    create_user,
    authenticate_user,
    get_users_with_pagination,
    delete_user
)
from app.middleware.logger import log_user_activity

router = APIRouter()

@router.post("/users/register", response_model=UserSchema, tags=["Users"])
def register_user(user: UserSchema, db: Session = Depends(get_db)):
    try:
        new_user = create_user(db, user)
        log_user_activity(db, user.username, "User registration")
        return UserSchema(username=new_user.username, password="", role=new_user.role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/users/login", response_model=TokenSchema, tags=["Users"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    log_user_activity(db, user.username, "User login")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserSchema, tags=["Users"])
def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_username(db, current_user['username'])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    log_user_activity(db, current_user['username'], "User profile view")
    return UserSchema(username=user.username, password="", role=user.role)

@router.get("/admin/activities", response_model=List[UserActivitySchema], tags=["Admin"])
def get_user_activities(
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
    page: int = 1,
    page_size: int = 10
):
    offset = (page - 1) * page_size
    activities = db.query(UserActivity).limit(page_size).offset(offset).all()
    return activities

@router.get("/admin/users", response_model=List[ViewUserSchema], tags=["Admin"])
def read_users(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    users = get_users_with_pagination(db, page, page_size)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

@router.delete("/admin/users/{username}", tags=["Admin"])
def remove_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    try:
        delete_user(db, username)
        log_user_activity(db, current_user['username'], f"Deleted user {username}")
        return {"message": f"User '{username}' has been successfully deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
