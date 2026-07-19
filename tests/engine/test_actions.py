"""Tests for the action types (hanoi.engine.actions).

Actions are player-relative: a pole is 1/2/3 (2 = SHARED), never a physical
pole. The player who acts is passed separately to step(), not carried here.
"""

import pytest
from pydantic import TypeAdapter, ValidationError

from hanoi.engine.actions import Action, Lift, Place, Skip


def test_lift_has_kind_and_pole():
    a = Lift(pole=1)
    assert a.kind == "lift"
    assert a.pole == 1


def test_place_has_kind_and_pole():
    a = Place(pole=3)
    assert a.kind == "place"
    assert a.pole == 3


def test_skip_has_kind_and_no_pole():
    a = Skip()
    assert a.kind == "skip"
    assert not hasattr(a, "pole")


@pytest.mark.parametrize("action", [Lift(pole=2), Place(pole=1), Skip()])
def test_actions_are_immutable(action):
    with pytest.raises(ValidationError):
        action.kind = "changed"


@pytest.mark.parametrize("bad_pole", [0, 4, -1])
def test_lift_rejects_out_of_range_pole(bad_pole):
    # pole must be 1, 2, or 3 (player-relative)
    with pytest.raises(ValidationError):
        Lift(pole=bad_pole)


@pytest.mark.parametrize(
    "payload, expected_type",
    [
        ({"kind": "lift", "pole": 1}, Lift),
        ({"kind": "place", "pole": 2}, Place),
        ({"kind": "skip"}, Skip),
    ],
)
def test_action_union_discriminates_by_kind(payload, expected_type):
    # The Action union parses the right concrete type from the "kind" tag.
    parsed = TypeAdapter(Action).validate_python(payload)
    assert isinstance(parsed, expected_type)


def test_action_json_round_trips():
    adapter = TypeAdapter(Action)
    for action in (Lift(pole=1), Place(pole=3), Skip()):
        restored = adapter.validate_json(adapter.dump_json(action))
        assert restored == action
