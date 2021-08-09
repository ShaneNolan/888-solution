from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, NewType, Optional, Type

from pydantic import BaseModel, validator

from app.enums import Entities, OutcomeEnum, StatusEnum, TypeEnum

ForeignKey = NewType('ForeignKey', int)


class ISchema(ABC):
    @abstractmethod
    def get_id(self) -> Optional[int]:
        ...

    @abstractmethod
    def set_id(self, id: int) -> None:
        ...

    @classmethod
    @abstractmethod
    def schema_json(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def construct(cls, **values: Any) -> Any: # noqa: WPS110
        ...

    @classmethod
    @abstractmethod
    def dict(cls) -> Dict[str, Any]:
        ...


class Schema(BaseModel, ISchema, ABC):
    ID: Optional[int]

    def get_id(self) -> Optional[int]:
        return self.ID

    def set_id(self, id: int) -> None:
        self.ID = id


class SportSchema(Schema):
    Name: str
    Slug: str
    Active: bool


class EventSchema(Schema):
    Name: str
    Slug: str
    Active: bool
    Type: TypeEnum
    Sport: ForeignKey = ForeignKey(0)  # Reference: SportSchema
    Status: StatusEnum
    ScheduledStart: datetime

    class Config:
        use_enum_values = True


class SelectionSchema(Schema):
    Name: str
    Event: ForeignKey = ForeignKey(0)  # Reference: Event
    Price: float
    Active: bool
    Outcome: OutcomeEnum

    class Config:
        use_enum_values = True

    @classmethod
    @validator('Price')
    def price_must_be_two_decimals(cls, price: float) -> float:
        DECIMAL_PLACES = 2

        price_str = str(price)

        if len(price_str[price_str.rfind('.') + 1:]) > DECIMAL_PLACES:
            raise ValueError(
                f'must be {DECIMAL_PLACES} decimal places or less.',
            )
        return price


class SchemaFactory:
    _schemas: Dict[str, Type[Schema]] = {
        Entities.Sport.value: SportSchema,
        Entities.Event.value: EventSchema,
        Entities.Selection.value: SelectionSchema,
    }

    @classmethod
    def create(cls, schema: str, **kwargs) -> ISchema:
        if schema in cls._schemas:
            return cls._schemas[schema](**kwargs)
        raise KeyError(schema)
