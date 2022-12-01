# generated by datamodel-codegen:
#   filename:  force.json
#   timestamp: 2022-11-25T05:45:15+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Force(BaseModel):
    __root__: List[float] = Field(
        ...,
        description="Force [Fx, Fy, Fz] (N) acting on a body with respect to the body's BF frame of reference.",
        max_items=3,
        min_items=3,
        title='Force',
    )
