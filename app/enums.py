from enum import Enum
from typing import Dict


class Entities(str, Enum):
    Sport = "sport"
    Event = "event"
    Selection = "selection"


class Operators(Enum):
    """
    Additional operators can be easily added such as REGEXP, ADD, etc.
    """

    Equals = "="
    NotEquals = "!="
    GreaterThan = ">"
    LessThan = "<"

    @classmethod
    def get_operators(cls) -> Dict[str, "Operators"]:
        return {
            operator.value: operator
            for operator_name, operator in cls.__members__.items()
        }


class OutcomeEnum(str, Enum):
    Lose = "Lose"
    Unsettled = "Unsettled"
    Void = "Void"
    Win = "Win"


class TypeEnum(str, Enum):
    Inplay = "Inplay"
    Preplay = "Preplay"

    def __str__(self) -> str:
        return str(self.value)


class StatusEnum(str, Enum):
    Cancelled = "Cancelled"
    Ended = "Ended"
    Started = "Started"
    Pending = "Pending"
