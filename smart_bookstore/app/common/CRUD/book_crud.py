from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.common.database.models import Book, Author, UserPreference
from app.schemas.book import BookSchema

def get_books(db: Session):
    return db.query(Book).all()

def get_book_by_id(db: Session, book_id: int):
    return db.query(Book).filter(Book.book_id == book_id).first()

def create_book(db: Session, book: BookSchema):
    db_author = db.query(Author).filter(Author.author_id == book.author_id).first()
    if not db_author:
        raise HTTPException(status_code=400, detail="Author not found")
    
    db_book = Book(
        book_id = book.book_id,
        title=book.title,
        author_id=book.author_id,
        genre=book.genre,
        description=book.description
    )
    try:
            db.add(db_book)
            db.commit()
            db.refresh(db_book)
    except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Book already exists")

    return db_book

def update_book(db: Session, book_id: int, book: BookSchema):
    db_book = db.query(Book).filter(Book.book_id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db_author = db.query(Author).filter(Author.author_id == book.author_id).first()
    if not db_author:
        raise HTTPException(status_code=404, detail="Author not found")

    db_book.book_id = book.book_id
    db_book.title = book.title
    db_book.author_id = book.author_id
    db_book.genre = book.genre
    db_book.description = book.description

    try:
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Book already exists")

    return db_book
def delete_book(db: Session, book_id: int):
    db_book = db.query(Book).filter(Book.book_id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(db_book)
    db.commit()
    return {"message": "Book deleted successfully"}

def get_recommended_books(db: Session, username: str) -> List[Book]:
    user_preferences = db.query(UserPreference).filter(UserPreference.username == username).all()
    preferred_genres = [pref.preference_value for pref in user_preferences if pref.preference_type == "genre"]

    if not preferred_genres:
        raise ValueError("No preferred genres found for user")

    recommended_books = db.query(Book).filter(Book.genre.in_(preferred_genres)).all()

    if not recommended_books:
        raise ValueError("No books found for preferred genres")

    return recommended_books