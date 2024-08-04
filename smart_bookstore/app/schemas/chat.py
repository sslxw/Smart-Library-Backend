from typing import Sequence, TypedDict
from pydantic import BaseModel
from langchain_core.messages import BaseMessage

class QueryRequest(BaseModel):
    query: str

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    intent: str