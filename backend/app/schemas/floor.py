from pydantic import BaseModel


class FloorCreate(BaseModel):
    building_id: int
    floor_label: str


class FloorUpdate(BaseModel):
    building_id: int
    floor_label: str


class FloorResponse(BaseModel):
    id: int
    building_id: int
    floor_label: str
    is_active: bool