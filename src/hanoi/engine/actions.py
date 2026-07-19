"""Player actions: Lift, Place, Skip.

Player-relative: `pole` is 1/2/3 (2 = SHARED). The acting player is passed
separately to step(), never carried on the action.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from hanoi.engine.state import LocalPole


class _Action(BaseModel):
    """Shared config: immutable, and strict about unknown fields.

    `extra="forbid"` rejects malformed input at the boundary — e.g. a skip that
    carries a pole, or an action with junk fields — instead of silently ignoring.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


class Lift(_Action):
    kind: Literal["lift"] = "lift"
    pole: LocalPole


class Place(_Action):
    kind: Literal["place"] = "place"
    pole: LocalPole


class Skip(_Action):
    kind: Literal["skip"] = "skip"


Action = Annotated[Lift | Place | Skip, Field(discriminator="kind")]
