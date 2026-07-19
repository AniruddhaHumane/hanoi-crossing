"""Player actions: Lift, Place, Skip.

Player-relative: `pole` is 1/2/3 (2 = SHARED). The acting player is passed
separately to step(), never carried on the action.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from hanoi.engine.state import LocalPole


class Lift(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal["lift"] = "lift"
    pole: LocalPole


class Place(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal["place"] = "place"
    pole: LocalPole


class Skip(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal["skip"] = "skip"


Action = Annotated[Lift | Place | Skip, Field(discriminator="kind")]
