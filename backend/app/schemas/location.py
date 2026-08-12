from pydantic import BaseModel


class LocationCreate(BaseModel):
    floor_id: int | None = None
    name: str
    location_type: str


class LocationUpdate(BaseModel):
    floor_id: int | None = None
    name: str
    location_type: str


class LocationResponse(BaseModel):
    id: int
    floor_id: int | None
    name: str
    location_type: str
    is_active: bool