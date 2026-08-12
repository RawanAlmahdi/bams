from pydantic import BaseModel


class ManufacturerCreate(BaseModel):
    name: str


class ManufacturerUpdate(BaseModel):
    name: str


class ManufacturerResponse(BaseModel):
    id: int
    name: str
    is_active: bool