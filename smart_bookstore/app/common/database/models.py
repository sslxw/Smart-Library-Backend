from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.common.database.database import Base

class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    password_hash = Column(String)
    role = Column(String)

    preferences = relationship("UserPreference", back_populates="user")
    activities = relationship("UserActivity", back_populates="user")

class UserPreference(Base):
    __tablename__ = "userpreferences"

    preference_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"))
    preference_type = Column(String)
    preference_value = Column(String)

    user = relationship("User", back_populates="preferences")

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"))
    activity = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activities")

class Author(Base):
    __tablename__ = "authors"

    author_id = Column(Integer, primary_key=True, index=True)
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

    author = relationship("Author", back_populates="books")
