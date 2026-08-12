"""State definitions for the ChallengeABM model."""

from enum import Enum


class State(str, Enum):
    UNAWARE = "U"
    OBSERVING = "O"
    PARTICIPATING = "P"
    AMPLIFYING = "A"
    COUNTERACTING = "C"
    DROPPED_OUT = "D"

