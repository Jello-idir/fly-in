from pydantic import BaseModel, Field
from Common import ZoneType, ColorType, HubType


class DroneBase(BaseModel):
    """A drone identifier and its initial grid coordinates."""
    id: int
    coord: tuple[int, int]


class HubMetadata(BaseModel):
    """A hub's zone, display color, and positive capacity."""
    zone: ZoneType = ZoneType.normal
    color: ColorType = ColorType.none
    max_drones: int = Field(default=1, gt=0)


class HubBase(BaseModel):
    """A named hub with a role, grid position, and metadata."""
    name: str
    type: HubType
    pos: tuple[int, int]
    metadata: HubMetadata = HubMetadata()


class ConnectionBase(BaseModel):
    """An undirected hub connection with a positive capacity."""
    hub_a: str
    hub_b: str
    link_capacity: int = Field(default=1, gt=0)
