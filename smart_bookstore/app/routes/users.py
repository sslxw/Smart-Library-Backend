from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from app.common.database.database import get_db
from app.common.database.models import User, UserActivity, UserPreference
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
    page_size: int = 10,
    username: str = None
):
    offset = (page - 1) * page_size
    query = db.query(UserActivity)
    
    if username:
        query = query.join(User).filter(User.username.ilike(f'%{username}%'))
    
    return query.limit(page_size).offset(offset).all()


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

@router.delete("/admin/users/{username}", tags=["Admin"]) # add the func to user_crud
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
    
@router.post("/users/preferences/genres", tags=["Users"])  # add the func to user_crud
def update_user_genres(genres: List[str], db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_preferences = db.query(UserPreference).filter(UserPreference.username == current_user['username'], UserPreference.preference_type == "genre").all()
    existing_genres = {pref.preference_value for pref in user_preferences}

    # Determine genres to add and remove
    genres_to_add = set(genres) - existing_genres
    genres_to_remove = existing_genres - set(genres)

    # Add new genres
    for genre in genres_to_add:
        new_preference = UserPreference(username=current_user['username'], preference_type="genre", preference_value=genre)
        db.add(new_preference)

    # Remove unselected genres
    for genre in genres_to_remove:
        db.query(UserPreference).filter(UserPreference.username == current_user['username'], UserPreference.preference_type == "genre", UserPreference.preference_value == genre).delete()

    db.commit()
    return {"message": "User genres updated successfully"}



