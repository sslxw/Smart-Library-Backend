from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.common.database.models import Book, Author, UserLikedBook, UserPreference
from app.schemas.book import ModBookSchema, BookSchema

def get_books(db: Session, page: int, page_size: int) -> List[Book]:
    offset = (page - 1) * page_size
    return db.query(Book).limit(page_size).offset(offset).all()

def get_book_by_id(db: Session, book_id: int) -> Book:
    return db.query(Book).filter(Book.book_id == book_id).first()

def create_book(db: Session, book: ModBookSchema) -> Book:
    db_author = db.query(Author).filter(Author.author_id == book.author_id).first()
    if not db_author:
        raise HTTPException(status_code=400, detail="Author not found")
    
    db_book = Book(
        title=book.title,
        author_id=book.author_id,
        genre=book.genre,
        description=book.description,
        average_rating=book.average_rating,
        published_year=book.published_year,
        cover=book.cover
    )
    try:
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Book already exists")

    return db_book

def update_book(db: Session, book_id: int, book: BookSchema) -> Book:
    db_book = db.query(Book).filter(Book.book_id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db_author = db.query(Author).filter(Author.author_id == book.author_id).first()
    if not db_author:
        raise HTTPException(status_code=404, detail="Author not found")

    db_book.title = book.title
    db_book.author_id = book.author_id
    db_book.genre = book.genre
    db_book.description = book.description
    db_book.average_rating = book.average_rating
    db_book.published_year = book.published_year
    db_book.cover = book.cover

    try:
        db.commit()
        db.refresh(db_book)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Book with this data already exists")

    return db_book

def delete_book(db: Session, book_id: int) -> dict:
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
        raise HTTPException(status_code=404, detail="No preferred genres found for user")

    recommended_books = db.query(Book).filter(Book.genre.in_(preferred_genres)).all()

    if not recommended_books:
        raise HTTPException(status_code=404, detail="No books found for preferred genres")

    return recommended_books

def get_book_by_title(db: Session, title: str, page: int, page_size: int) -> List[Book]:
    offset = (page - 1) * page_size
    return db.query(Book).filter(Book.title.ilike(f"%{title}%")).offset(offset).limit(page_size).all()

def get_books_sorted(db: Session, order: str, page: int, page_size: int) -> List[Book]:
    order_by_clause = Book.average_rating.asc() if order == 'asc' else Book.average_rating.desc()
    return db.query(Book).order_by(order_by_clause).offset((page - 1) * page_size).limit(page_size).all()

def like_book(db: Session, username: str, book_id: int) -> UserLikedBook:
    db_book = db.query(Book).filter(Book.book_id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    user_liked_book = UserLikedBook(username=username, book_id=book_id)

    try:
        db.add(user_liked_book)
        db.commit()
        db.refresh(user_liked_book)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already liked this book")

    return user_liked_book

def unlike_book(db: Session, username: str, book_id: int) -> dict:
    user_liked_book = db.query(UserLikedBook).filter(UserLikedBook.username == username, UserLikedBook.book_id == book_id).first()
    if not user_liked_book:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(user_liked_book)
    db.commit()
    return {"message": "Book unliked successfully"}

def get_liked_books(db: Session, username: str) -> List[Book]:
    liked_books = db.query(UserLikedBook).filter(UserLikedBook.username == username).all()
    book_ids = [like.book_id for like in liked_books]
    return db.query(Book).filter(Book.book_id.in_(book_ids)).all()

def get_books_by_publish_year(db: Session, order: str, page: int, page_size: int) -> List[Book]:
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order parameter. Use 'asc' or 'desc'.")
    
    order_by_clause = Book.published_year.asc() if order == "asc" else Book.published_year.desc()
    books = db.query(Book).order_by(order_by_clause).offset((page - 1) * page_size).limit(page_size).all()
    
    if not books:
        raise HTTPException(status_code=404, detail="No books found")
    
    return books
