from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.common.database.database import get_db
from app.schemas.book import ModBookSchema, BookSchema
from app.middleware.auth import get_current_user, admin_required
from app.middleware.logger import log_user_activity
from app.common.CRUD.book_crud import get_books, get_book_by_id, get_recommended_books, delete_book, create_book, update_book, get_book_by_title, get_books_sorted

router = APIRouter()

# @router.get("/books", response_model=List[BookSchema], tags=["Books"], operation_id="get_books_list")
# def get_all_books(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), page: int = 1, page_size: int = 1):
#     log_user_activity(db, current_user['username'], "Searched for all books")
#     return get_books(db, page, page_size)

@router.get("/books", response_model=List[BookSchema], tags=["Books"], operation_id="get_books_list")
def get_all_books(db: Session = Depends(get_db), page: int = 1, page_size: int = 1):
    return get_books(db, page, page_size)

@router.get("/books/{book_id}", response_model=BookSchema, tags=["Books"], operation_id="get_book_by_title")
def get_book(book_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    book = get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=200, detail="Book not found")
    log_user_activity(db, current_user['username'], f"Searched for book with id: {book_id}")
    return book

@router.post("/books", response_model=ModBookSchema, tags=["Books"], operation_id="create_book_record")
def create_books(book: ModBookSchema, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    log_user_activity(db, current_user['username'], "Book creation")
    return create_book(db, book)

@router.put("/books/{book_id}", response_model=BookSchema, tags=["Books"], operation_id="update_book_record")
def update_books(book_id: int, book: BookSchema, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    log_user_activity(db, current_user['username'], "Book update")
    return update_book(db, book_id, book)

@router.delete("/books/{book_id}", tags=["Books"])
def delete_books(book_id: int, db: Session = Depends(get_db), current_user: dict = Depends(admin_required)):
    log_user_activity(db, current_user['username'], "Book deletion")
    return delete_book(db, book_id)

@router.get("/recommendations", response_model=List[BookSchema], tags=["Recommendations"])
def get_recommended_books_route(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        log_user_activity(db, current_user['username'], "Viewed their recommendations")
        return get_recommended_books(db, current_user["username"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/books/title/{title}", response_model=List[BookSchema], tags=["Books"], operation_id="get_book_by_title")
def get_book_by_title_route(title: str, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    books = get_book_by_title(db, title, page, page_size)
    if not books:
        raise HTTPException(status_code=404, detail="No books found")
    return [BookSchema.model_validate(book) for book in books]

@router.get("/books/sorted_by_rating/{order}", response_model=List[BookSchema], tags=["Books"], operation_id="get_books_sorted_by_rating")
def get_books_sorted_by_rating(order: str, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    print(f"Order: {order}, Page: {page}, Page Size: {page_size}")  # Debugging line
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order parameter. Use 'asc' or 'desc'.")
    return get_books_sorted(db, order, page, page_size)