from datetime import datetime
from typing import cast

import pytest

from app.enums import OutcomeEnum, StatusEnum, TypeEnum
from app.models import (
    BaseModel,
    EventModel,
    Operators,
    SelectionModel,
    SportModel,
)
from app.schemas import EventSchema, ISchema, SelectionSchema, SportSchema

def test_select_fields(sport_testing_schema: SportSchema) -> None:
    sm = SportModel().select_fields('Name', 'Slug')
    
    assert len(sm) > 0
    assert sm[0].get_id() != None
    

@pytest.mark.parametrize("schema, model", [
        (SportSchema(Name="isport", Slug="is", Active=True), SportModel()),
        (
            EventSchema(
                Name='ievent',
                Slug='ie',
                Active=True,
                Type=TypeEnum.Inplay,
                Sport=1,
                Status=StatusEnum.Pending,
                ScheduledStart=datetime.now()
            ),
            EventModel()
        ),
        (
            SelectionSchema(
                Name='iselection',
                Event=1,
                Price=10.10,
                Active=True,
                Outcome=OutcomeEnum.Unsettled,
            ),
            SelectionModel()
        )
    ]
)
def test_insert(schema: ISchema, model: BaseModel) -> None:
    inserted_schema = model.insert(schema)

    assert inserted_schema.get_id() != None

    assert len(model.select('ID').filter('ID', Operators.Equals, inserted_schema.ID).execute()) == 1

def test_complex_sport_query() -> None:
    ss = SportSchema(Name="test_two", Slug="test_two", Active=True)
    sm = SportModel()
    sm.insert(ss)

    sm = SportModel().select('Name', 'Slug', 'Active').filter('Name', Operators.Equals, "test_two")
    assert sm.get_query() == "SELECT ID, Name, Slug, Active FROM sports WHERE Name = 'test_two'"

    sport_models = sm.execute()[0]
    assert sport_models.Name == "test_two"
    assert len(SportModel().select('ID').filter('ID', Operators.Equals, sport_models.get_id()).execute()) == 1


@pytest.mark.parametrize("model, id", 
    [
        (SportModel(), 1),
        (EventModel(), 1),
        (SelectionModel(), 1)
    ]
)
def test_find(model: BaseModel, id: int) -> None:
    schema = model.find(id)

    assert schema.get_id() == id

def test_update_sport() -> None:
    ss = SportSchema(
        Name='Update_Test',
        Slug='UTest',
        Active=True,
    )
    sm = SportModel()
    ss = sm.insert(ss)

    assert ss.get_id() != None

def test_update_event() -> None:
    ss = SportSchema(
        Name='Update_Test',
        Slug='UTest',
        Active=True,
    )
    sm = SportModel()
    ss = sm.insert(ss)

    es = EventSchema(
        Name='Update_Test',
        Slug='UTest',
        Active=True,
        Type=TypeEnum.Inplay,
        Sport=ss.get_id(),
        Status=StatusEnum.Pending,
        ScheduledStart=datetime.now(),
    )
    em = EventModel()
    es = em.insert(es)
    es = cast(EventSchema, es)
    assert es.get_id() != None

    es.Active = False
    es = em.update(es)
    es = cast(EventSchema, es)

    assert es.Active == False

    updated_ss = sm.select('ID', 'Active').filter('ID', Operators.Equals, ss.get_id()).execute()[0]
    updated_ss = cast(SportSchema, updated_ss)
    assert updated_ss.Active == False

def test_update_selection() -> None:
    """Test can be refactored into a single test for both event and selection but I decided not to
        for increased readability.
    """

    es = EventSchema(
        Name='Update_Test',
        Slug='UTest',
        Active=True,
        Type=TypeEnum.Inplay,
        Sport=1,
        Status=StatusEnum.Pending,
        ScheduledStart=datetime.now(),
    )
    em = EventModel()
    es = em.insert(es)

    ss = SelectionSchema(
        Name='Testing',
        Event=es.get_id(),
        Price=10.10,
        Active=True,
        Outcome=OutcomeEnum.Unsettled,
    )
    sm = SelectionModel()
    ss = sm.insert(ss)
    ss = cast(SelectionSchema, ss)

    assert ss.get_id() != None
    
    ss.Active = False
    ss = sm.update(ss)
    ss = cast(SelectionSchema, ss)

    assert ss.Active == False

    updated_es = em.select('ID', 'Active').filter('ID', Operators.Equals, es.get_id()).execute()[0]
    updated_es = cast(EventSchema, updated_es)
    assert updated_es.Active == False
