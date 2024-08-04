from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.common.database.models import Author
from app.schemas.author import AuthorSchema

def get_authors(db: Session, page, page_size):
    offset = (page - 1) * page_size
    return db.query(Author).limit(page_size).offset(offset).all()

def get_author_by_id(db: Session, author_id: int) -> Author:
    return db.query(Author).filter(Author.author_id == author_id).first()

def create_author(db: Session, author: AuthorSchema) -> Author:
    
    db_author = Author(
        name=author.name,
        biography=author.biography
    )
    
    try:
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Author already exists")

    return db_author

def update_author(db: Session, author_id: int, author: AuthorSchema) -> Author:
    db_author = db.query(Author).filter(Author.author_id == author_id).first()
    if not db_author:
        raise ValueError("Author not found")

    db_author.name = author.name
    db_author.biography = author.biography

    try:
        db.commit()
        db.refresh(db_author)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Author already exists")

    return db_author


def delete_author(db: Session, author_id: int) -> None:
    db_author = db.query(Author).filter(Author.author_id == author_id).first()
    if not db_author:
        raise ValueError("Author not found")
    
    db.delete(db_author)
    db.commit()
