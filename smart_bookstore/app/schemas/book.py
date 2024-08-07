from pydantic import BaseModel, ConfigDict
from typing import Optional

class BookSchema(BaseModel):
    book_id: int
    title: str
    author_id: int
    genre: Optional[str] = None
    description: Optional[str] = None
    average_rating: Optional[float] = None
    published_year: Optional[int] = None
    cover: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ModBookSchema(BaseModel):
    title: str
    author_id: int
    genre: Optional[str] = None
    description: Optional[str] = None
    average_rating: Optional[float] = None
    published_year: Optional[int] = None
    cover: Optional[str] = None

class UserLikedBook(BaseModel):
    username: str
    book_id: int

