from pydantic import BaseModel


class EquipmentTypeCreate(BaseModel):
    category_id: int
    name: str
    description: str | None = None


class EquipmentTypeUpdate(BaseModel):
    category_id: int
    name: str
    description: str | None = None


class EquipmentTypeResponse(BaseModel):
    id: int
    category_id: int
    name: str
    description: str | None
    is_active: bool