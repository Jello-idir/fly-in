from pydantic import BaseModel, Field
from Common import ZoneType, ColorType, HubType


class DroneBase(BaseModel):
    """A drone identifier and its initial grid coordinates.

    Attributes:
        id: Unique drone identifier.
        coord: Initial grid coordinates as (x, y).
    """

    id: int
    coord: tuple[int, int]


class HubMetadata(BaseModel):
    """A hub's zone, display color, and positive capacity.

    Attributes:
        zone: Zone access rule and movement cost category.
        color: Packed RGBA color or special rainbow marker.
        max_drones: Positive simultaneous hub capacity; defaults to one.
    """

    zone: ZoneType = ZoneType.normal
    color: ColorType = ColorType.none
    max_drones: int = Field(default=1, gt=0)


class HubBase(BaseModel):
    """A named hub with a role, grid position, and metadata.

    Attributes:
        name: Unique hub name.
        type: Start, intermediate, or destination role.
        pos: Grid coordinates as (x, y).
        metadata: Zone, color, and occupancy settings.
    """

    name: str
    type: HubType
    pos: tuple[int, int]
    metadata: HubMetadata = HubMetadata()


class ConnectionBase(BaseModel):
    """An undirected hub connection with a positive capacity.

    Attributes:
        hub_a: First endpoint name.
        hub_b: Second endpoint name.
        link_capacity: Positive simultaneous crossing capacity; defaults to
            one.
    """

    hub_a: str
    hub_b: str
    link_capacity: int = Field(default=1, gt=0)
