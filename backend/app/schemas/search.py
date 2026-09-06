from pydantic import BaseModel


class SearchResult(BaseModel):
    kind: str
    id: int
    title: str
    context: str
    status: str | None = None
