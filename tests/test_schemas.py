from datetime import datetime
from app.schemas import EventSchema, SchemaFactory, SelectionSchema, SportSchema
import pytest
from datetime import datetime
from app.enums import Entities
from typing import cast

def test_selection_price() -> None:
    INVALID_PRICE = 11.111111
    with pytest.raises(ValueError):
        SelectionSchema(
            Name='test',
            Event=EventSchema(
                Name='test', 
                Slug='test',
                Active=True,
                Type='Inplay',
                Sport=SportSchema(Name='test', Slug='test', Active=True),
                Status='Pending',
                ScheduledStart=datetime.now()
            ),
            Price=INVALID_PRICE,
            Active=True,
            Outcome='Unsettled'
        )

def test_schema_factory() -> None:
    Name, Slug, Active = 'testing', 'test', True

    sport = SchemaFactory.create(Entities.Sport.value, **{'Name': Name, 'Slug': Slug, 'Active': Active})
    sport = cast(SportSchema, sport)

    assert sport.Name == Name
    assert sport.Slug == Slug
    assert sport.Active == Active