from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    parent_id: int | None = None


class LinkResearch(BaseModel):
    project_id: int


class EndorseResearch(BaseModel):
    label: str = Field(default="Endorsed", max_length=100)
