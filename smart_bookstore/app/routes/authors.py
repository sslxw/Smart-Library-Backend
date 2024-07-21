from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.common.database.database import get_db
from app.schemas.author import AuthorSchema
from app.middleware.auth import get_current_user, admin_required
from app.middleware.logger import log_user_activity
from app.common.CRUD.author_crud import get_authors, get_author_by_id, create_author, update_author, delete_author

router = APIRouter()

@router.get("/authors", response_model=List[AuthorSchema], tags=["Authors"], operation_id="get_authors_list")
def get_authors_route(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    log_user_activity(db, current_user['username'], "Searched for all authors")
    return get_authors(db)

@router.get("/authors/{author_id}", response_model=AuthorSchema, tags=["Authors"], operation_id="get_author_by_id")
def get_author_route(author_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    author = get_author_by_id(db, author_id)
    log_user_activity(db, current_user['username'], f"Searched for author with ID: {author_id}")

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

@router.post("/authors", response_model=AuthorSchema, tags=["Authors"], operation_id="create_author_record")
def create_author_route(author: AuthorSchema, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    log_user_activity(db, current_user['username'], "Author creation")
    return create_author(db, author)

@router.put("/authors/{author_id}", response_model=AuthorSchema, tags=["Authors"], operation_id="update_author_record")
def update_author_route(author: AuthorSchema, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    try:
        updated_author = update_author(db, author.author_id, author)
        log_user_activity(db, current_user['username'], "Author update")
        return updated_author
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/authors/{author_id}", tags=["Authors"], operation_id="delete_author_record")
def delete_author_route(author_id: int, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    try:
        delete_author(db, author_id)
        log_user_activity(db, current_user['username'], "Author deletion")
        return {"message": "Author deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
