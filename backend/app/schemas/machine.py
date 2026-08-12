from pydantic import BaseModel


class MachineCreate(BaseModel):
    serial_number: str
    asset_tag: str | None = None
    name: str
    model: str | None = None
    manufacturer_id: int | None = None
    equipment_type_id: int | None = None
    location_id: int | None = None
    status: str = "NEW"
    condition: str = "NEW"


class MachineUpdate(BaseModel):
    asset_tag: str | None = None
    name: str
    model: str | None = None
    manufacturer_id: int | None = None
    equipment_type_id: int | None = None
    location_id: int | None = None
    status: str
    condition: str


class MachineResponse(BaseModel):
    id: int
    serial_number: str
    asset_tag: str | None
    name: str
    model: str | None
    manufacturer_id: int | None
    equipment_type_id: int | None
    location_id: int | None
    status: str
    condition: str
    is_active: bool