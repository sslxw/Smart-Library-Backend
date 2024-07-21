from pydantic import BaseModel
from typing import Optional

class BookSchema(BaseModel):
    book_id: int
    title: str
    author_id: int
    genre: Optional[str] = None
    description: Optional[str] = None
