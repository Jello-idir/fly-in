from pydantic import BaseModel, Field, model_validator
from Common import ZoneType, ColorType, HubType
from typing import Any


class Drone(BaseModel):
    id: int
    pos: tuple[int, int]
    color: ColorType = ColorType.white


class HubMetadata(BaseModel):
    zone: ZoneType = ZoneType.normal
    color: ColorType = ColorType.none
    max_drones: int = Field(default=1, gt=0)


class Hub(BaseModel):
    name: str
    type: HubType
    pos: tuple[int, int]
    metadata: HubMetadata = HubMetadata()
    drones: list[Drone]


class Connection(BaseModel):
    hub_a: str
    hub_b: str
    capacity: int = Field(default=1, gt=0)

    @model_validator(mode="after")
    def no_self_loop(self):
        if self.hub_a == self.hub_b:
            raise ValueError("self loop detected.")
        return self



