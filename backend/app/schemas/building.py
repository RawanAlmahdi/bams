from pydantic import BaseModel


class BuildingCreate(BaseModel):
    name: str


class BuildingUpdate(BaseModel):
    name: str


class BuildingResponse(BaseModel):
    id: int
    name: str
    is_active: bool