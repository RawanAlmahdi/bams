from pydantic import BaseModel


class EquipmentCategoryCreate(BaseModel):
    name: str
    description: str | None = None


class EquipmentCategoryUpdate(BaseModel):
    name: str
    description: str | None = None


class EquipmentCategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool