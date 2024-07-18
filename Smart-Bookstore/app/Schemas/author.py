from pydantic import BaseModel
from typing import Optional

class AuthorSchema(BaseModel):
    author_id: int
    name: str
    biography: Optional[str] = None