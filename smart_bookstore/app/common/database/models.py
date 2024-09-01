from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, create_engine
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.common.database.database import Base

class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    password_hash = Column(String)
    role = Column(String)

    preferences = relationship("UserPreference", back_populates="user")
    activities = relationship("UserActivity", back_populates="user")
    liked_books = relationship("UserLikedBook", back_populates="user")
    activities = relationship("UserActivity", cascade="all, delete-orphan", back_populates="user")


class UserPreference(Base):
    __tablename__ = "userpreferences"

    preference_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, ForeignKey("users.username"))
    preference_type = Column(String)
    preference_value = Column(String)

    user = relationship("User", back_populates="preferences")

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"))
    activity = Column(String)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="activities")

class Author(Base):
    __tablename__ = "authors"

    author_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    biography = Column(String)

    books = relationship("Book", back_populates="author", cascade="all, delete-orphan")

class Book(Base):
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author_id = Column(Integer, ForeignKey("authors.author_id"))
    genre = Column(String)
    description = Column(String)
    average_rating = Column(Float)  
    published_year = Column(Integer)  
    cover = Column(String)  

    author = relationship("Author", back_populates="books")
    liked_by = relationship("UserLikedBook", back_populates="book")

class UserLikedBook(Base):
    __tablename__ = "user_liked_books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, ForeignKey("users.username"))
    book_id = Column(Integer, ForeignKey("books.book_id"))

    user = relationship("User", back_populates="liked_books")
    book = relationship("Book", back_populates="liked_by")
