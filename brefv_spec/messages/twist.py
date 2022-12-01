# generated by datamodel-codegen:
#   filename:  twist.json
#   timestamp: 2022-11-25T05:45:15+00:00

from __future__ import annotations

from pydantic import BaseModel, Extra

from . import angular_velocity, linear_velocity


class Twist(BaseModel):
    class Config:
        extra = Extra.forbid

    linear_velocity: linear_velocity.LinearVelocity
    angular_velocity: angular_velocity.AngularVelocity