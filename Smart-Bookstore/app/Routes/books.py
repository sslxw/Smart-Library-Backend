from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.Common.Database.database import get_db
from app.Schemas.book import BookSchema
from app.Common.Middleware.security import get_current_user, admin_required
from app.Common.Middleware.logger import log_user_activity
from app.Common.Services import book_services

router = APIRouter()

@router.get("/books", response_model=List[BookSchema], tags=["Books"], operation_id="get_books_list")
def get_books(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    log_user_activity(db, current_user['username'], "Searched for all books")
    return book_services.get_books(db)

@router.get("/books/{book_id}", response_model=BookSchema, tags=["Books"], operation_id="get_book_by_title")
def get_book(book_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    book = book_services.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=200, detail="Book not found")
    log_user_activity(db, current_user['username'], f"Searched for book with id: {book_id}")
    return book

@router.post("/books", response_model=BookSchema, tags=["Books"], operation_id="create_book_record")
def create_book(book: BookSchema, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    log_user_activity(db, current_user['username'], "Book creation")
    return book_services.create_book(db, book)

@router.put("/books/{book_id}", response_model=BookSchema, tags=["Books"], operation_id="update_book_record")
def update_book(book_id: int, book: BookSchema, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    log_user_activity(db, current_user['username'], "Book update")
    return book_services.update_book(db, book_id, book)

@router.delete("/books/{book_id}", tags=["Books"])
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    log_user_activity(db, current_user['username'], "Book deletion")
    return book_services.delete_book(db, book_id)

@router.get("/recommendations", response_model=List[BookSchema], tags=["Recommendations"])
def get_recommended_books_route(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        log_user_activity(db, current_user['username'], "Viewed their recommendations")
        return book_services.get_recommended_books(db, current_user["username"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
