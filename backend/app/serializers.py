from dataclasses import asdict
from .models import Fixture, Standing


def standing_from_dict(value: dict) -> Standing:
    return Standing(**value)


def fixture_from_dict(value: dict) -> Fixture:
    return Fixture(**value)


def result_to_dict(value):
    return asdict(value)
