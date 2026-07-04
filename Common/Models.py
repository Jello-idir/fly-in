from pydantic import BaseModel, Field
from Common import ZoneType, ColorType, HubType


class DroneBase(BaseModel):
    id: int
    coord: tuple[int, int]


class HubMetadata(BaseModel):
    zone: ZoneType = ZoneType.normal
    color: ColorType = ColorType.none
    max_drones: int = Field(default=1, gt=0)


class HubBase(BaseModel):
    name: str
    type: HubType
    pos: tuple[int, int]
    metadata: HubMetadata = HubMetadata()


class ConnectionBase(BaseModel):
    hub_a: str
    hub_b: str
    link_capacity: int = Field(default=1, gt=0)
