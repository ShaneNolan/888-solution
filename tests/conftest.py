from datetime import datetime

import pytest

from app.enums import OutcomeEnum, StatusEnum, TypeEnum
from app.models import (
    BaseModel,
    EventModel,
    SelectionModel,
    SelectionSchema,
    SportModel,
    create_database,
    remove_database,
)
from app.schemas import EventSchema, SelectionSchema, SportSchema


def create_event_testing_schema()  -> EventSchema:
    return EventSchema(
        ID=1,
        Name='Testing',
        Slug='Test',
        Active=True,
        Type=TypeEnum.Inplay,
        Sport=1,
        Status=StatusEnum.Pending,
        ScheduledStart=datetime.now(),
    )

def create_selection_testing_schema() -> SelectionSchema:
    return SelectionSchema(
        ID=1,
        Name='Testing',
        Event=1,
        Price=10.10,
        Active=True,
        Outcome=OutcomeEnum.Unsettled,
    )

def create_sport_testing_schema() -> SportSchema:
    return SportSchema(
        ID=1,
        Name='Testing',
        Slug='Test',
        Active=True,
    )

@pytest.fixture()
def event_testing_schema() -> EventSchema:
    return create_event_testing_schema()

@pytest.fixture()
def selection_testing_schema() -> SelectionSchema:
    return create_selection_testing_schema()

@pytest.fixture()
def sport_testing_schema() -> SportSchema:
    return create_sport_testing_schema()

@pytest.fixture(scope='session', autouse=True)
def database() -> None:
    KEY_DATABASE = 'database'

    DB_SETTINGS = {
        'host': 'localhost',
        'port': '3306',
        'user': 'root',
        'database': 'test_eight_app',
        'password': 'root'
    }

    BaseModel.db_settings = DB_SETTINGS

    db_settings_without_database = DB_SETTINGS.copy()
    database_name = db_settings_without_database[KEY_DATABASE] 
    del db_settings_without_database[KEY_DATABASE] 

    remove_database(db_settings_without_database, database_name) # If the tests crashed, etc.
    create_database(db_settings_without_database, database_name)

    SportModel().insert(create_sport_testing_schema())
    EventModel().insert(create_event_testing_schema())
    SelectionModel().insert(create_selection_testing_schema())

    yield

    remove_database(db_settings_without_database, database_name)

    