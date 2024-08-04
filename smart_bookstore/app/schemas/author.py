from pydantic import BaseModel
from typing import Optional

class AuthorSchema(BaseModel):
    name: str
    biography: Optional[str] = None