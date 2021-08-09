import json
from enum import Enum
from os import environ
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, cast

from mysql.connector import connect

from app.enums import Entities, Operators
from app.schemas import EventSchema, ISchema, SelectionSchema, SportSchema

DB_SETTINGS = {
    'host': environ.get('DB_HOST', 'localhost'),
    'port': environ.get('DB_PORT', '3306'),
    'user': 'root',
    'password': 'root',
    'database': 'eightapp',
}
## TODO: CREATE DATABASE FROM DOCKERFILE OR MAKE FILE. :)


def create_database(db_settings: Dict[str, Any], database_name: str) -> None:
    with connect(**db_settings) as connection:
        cursor = connection.cursor()
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS {database_name}')


def remove_database(db_settings: Dict[str, Any], database_name: str) -> None:
    with connect(**db_settings) as connection:
        cursor = connection.cursor()
        cursor.execute(f'DROP DATABASE IF EXISTS {database_name}')


class Keywords(str, Enum):
    ID = 'ID'

    Properties = 'properties'

    And = 'AND'
    From = 'FROM'
    InsertInto = 'INSERT INTO'
    Set = 'SET'
    Select = 'SELECT'
    Update = 'UPDATE'
    Values = 'VALUES'
    Where = 'WHERE'

class EmptyQuery(Exception):
    """Raised when `.execute()` is called without prior select/filter."""

class SchemaNotFound(Exception):
    """Raised when the requested Schema is not found."""

class BaseModel:
    db_settings: Dict[str, Any] = DB_SETTINGS
    table_name: str
    schema: Type[ISchema]

    table_created: bool = False

    BLANK_QUERY: str = ''

    def _create_table_if_not_exists(self) -> None:
        """Automatically create the provided schema table if it does not exist.

        For example::
            {
                "title":"SportSchema",
                "type":"object",
                "properties":{
                    "Name":{
                    "title":"Name",
                    "type":"string"
                    },
                    "Slug":{
                    "title":"Slug",
                    "type":"string"
                    },
                    "Active":{
                    "title":"Active",
                    "type":"boolean"
                    }
                },
                "required":[
                    "Name",
                    "Slug",
                    "Active"
                ]
            }

        Would result in the following create table query::
            CREATE TABLE IF NOT EXISTS sports (ID INTEGER PRIMARY KEY AUTO_INCREMENT, Name VARCHAR(255), Slug VARCHAR(255), Active BOOLEAN)
        """
        COLUMN_DEFINITIONS = 'definitions'
        COLUMN_TYPE = 'type'

        KEY_REF = '$ref'

        TYPE_LOOKUP = {
            'string': 'VARCHAR(255)',
            'integer': 'INTEGER',
            'boolean': 'BOOLEAN',
            'number': 'INTEGER',
        }

        def ref_lookup(
            property: Dict[str, Any], fields: Dict[str, Any]
        ) -> Dict[str, Any]:
            ref = property[KEY_REF]
            property_lookup_name = ref[ref.rfind('/') + 1 :]
            return fields[COLUMN_DEFINITIONS][property_lookup_name]

        field_queries = []
        fields = json.loads(self.schema.schema_json())

        del fields[Keywords.Properties.value][
            Keywords.ID.value
        ]  # Remove primary key field. It is handled with auto increment below.

        for property_name, property in fields[Keywords.Properties.value].items():
            if KEY_REF in property:
                property = ref_lookup(property, fields)
            field_queries.append(
                f'{property_name} {TYPE_LOOKUP[property[COLUMN_TYPE]]}'
            )
        table_columns = ', '.join(field_queries)

        with connect(**BaseModel.db_settings) as connection:
            cursor = connection.cursor()
            cursor.execute(
                f'CREATE TABLE IF NOT EXISTS {self.table_name} (ID INTEGER PRIMARY KEY AUTO_INCREMENT, {table_columns})'
            )
            self._table_created = True

    def __init__(self) -> None:
        self._table_created = False
        if not self.table_created:
            self._create_table_if_not_exists()
        self._query: str = BaseModel.BLANK_QUERY
        self._last_method_called: Optional[function] = None

    def _clean_selected_fields(self, field_names: Tuple[str, ...]) -> Tuple[str, ...]:
        """Remove duplicates, e.g. 'ID' field requested twice.

        Maintains order. Using a set doesn't maintain order.
        """
        list_field_names = [Keywords.ID.value]
        for field in field_names:
            if field in list_field_names:
                continue
            list_field_names.append(field)
        return tuple(list_field_names)

    def _append_to_query(self, statement: str) -> None:
        if self._query == BaseModel.BLANK_QUERY:
            fields = json.loads(self.schema.schema_json())
            field_names = ', '.join(fields[Keywords.Properties.value].keys())

            self._query = f'{Keywords.Select.value} {field_names} {Keywords.From.value} {self.table_name}'
        self._query += f' {statement}'

    def _map_results_to_schema(
        self, field_names: Iterable[str], results: List[Tuple[Any, ...]]
    ) -> List[ISchema]:
        schema_objects: List[ISchema] = []

        for result in results:
            row_data_mapped_to_fields = dict(zip(field_names, result))
            schema_objects.append(self.schema.construct(**row_data_mapped_to_fields))
        return schema_objects

    def _fields_from_schema(self, schema: ISchema) -> List[str]:
        return cast(List[str], schema.dict().keys())  # KeysView[str]

    def _values_from_schema(self, schema: ISchema) -> List[Any]:
        return cast(List[Any], schema.dict().values())  # KeysView[Any]

    def select_fields(self, *field_names) -> List[ISchema]:
        field_names = self._clean_selected_fields(field_names)

        fields_formatted = ', '.join(field_names)
        query = f'{Keywords.Select.value} {fields_formatted} {Keywords.From.value} {self.table_name}'

        with connect(**BaseModel.db_settings) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            return self._map_results_to_schema(field_names, results)

    def insert(self, schema: ISchema) -> ISchema:
        fields = self._fields_from_schema(schema)
        field_names = ', '.join(self._fields_from_schema(schema))
        fields_placeholder = ('%s, ' * len(fields))[:-2]  # Remove trailing , .
        values = tuple(self._values_from_schema(schema))

        query = f'{Keywords.InsertInto.value} {self.table_name} ({field_names}) {Keywords.Values.value} ({fields_placeholder})'
        with connect(**BaseModel.db_settings) as connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()

            schema.set_id(cursor.lastrowid)
        return schema

    def update(self, schema: ISchema) -> ISchema:
        REMOVE_ID_FIELD_WITH_INDEX = 1

        field_names = list(self._fields_from_schema(schema))[
            REMOVE_ID_FIELD_WITH_INDEX:
        ]
        values = list(self._values_from_schema(schema))[REMOVE_ID_FIELD_WITH_INDEX:]
        fields_placeholder = ', '.join(
            [f'{field_name} = %s' for field_name in field_names]
        )
        query = f"{Keywords.Update.value} {self.table_name} {Keywords.Set.value} {fields_placeholder} {Keywords.Where.value} {Keywords.ID.value} = '{schema.get_id()}'"

        with connect(**BaseModel.db_settings) as connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
        return schema

    def select(self, *field_names) -> 'BaseModel':
        field_names = self._clean_selected_fields(field_names)
        fields_formatted = ', '.join(field_names)

        self._query = f'{Keywords.Select.value} {fields_formatted} {Keywords.From.value} {self.table_name}'

        self._last_method_called = self.select
        return self

    def filter(self, field_name: str, operator: Operators, value: Any) -> 'BaseModel':
        expression = (
            Keywords.And.value
            if self._last_method_called == self.filter
            else Keywords.Where.value
        )

        query = f"{expression} {field_name} {operator.value} '{value}'"

        self._append_to_query(query)

        self._last_method_called = self.filter
        return self

    def execute(self) -> List[ISchema]:
        if self._query == BaseModel.BLANK_QUERY:
            raise EmptyQuery()

        field_names = list(
            map(
                str.strip,
                self._query[
                    self._query.find(Keywords.Select.value)
                    + len(Keywords.Select.value) : self._query.find(Keywords.From.value)
                ]
                .strip()
                .split(','),
            )
        )

        with connect(**BaseModel.db_settings) as connection:
            cursor = connection.cursor()
            cursor.execute(self._query)
            results = cursor.fetchall()

            self._query = BaseModel.BLANK_QUERY
            self._last_method_called = None

            return self._map_results_to_schema(field_names, results)

    def find(self, id: int) -> ISchema:
        self.filter(Keywords.ID.value, Operators.Equals, id)
        result = self.execute()

        if result:
            return result[0]
        raise SchemaNotFound(f'Not found, ID: {id}.')

    def get_query(self) -> str:
        return self._query


class SportModel(BaseModel):
    schema = SportSchema
    table_name = 'sports'


class EventModel(BaseModel):
    schema = EventSchema
    table_name = 'events'

    def update(self, schema: ISchema) -> ISchema:
        """When all the events of a sport are inactive,
            the sport becomes inactive
        """
        schema = super().update(schema)

        schema = cast(EventSchema, schema)
        if not schema.Active and schema.Sport > 0:
            self.select('ID', 'Sport', 'Active').filter(
                'Sport', Operators.Equals, schema.Sport,
            ).filter('Active', Operators.Equals, 1)
            result = self.execute()
            if not result:
                sm = SportModel()
                sport = sm.find(schema.Sport)
                sport = cast(SportSchema, sport)
                sport.Active = False
                sm.update(sport)
        return schema


class SelectionModel(BaseModel):
    schema = SelectionSchema
    table_name = 'selections'

    def update(self, schema: ISchema) -> ISchema:
        """When all the selections of a particular event are inactive,
            the event becomes inactive
        """
        schema = super().update(schema)

        schema = cast(SelectionSchema, schema)
        if not schema.Active and schema.Event > 0:
            self.select('ID', 'Event', 'Active').filter(
                'Event', Operators.Equals, schema.Event,
            ).filter('Active', Operators.Equals, 1)
            result = self.execute()
            if not result:
                em = EventModel()
                event = em.find(schema.Event)
                event = cast(EventSchema, event)
                event.Active = False
                em.update(event)
        return schema


class ModelFactory:
    _models: Dict[str, Type[BaseModel]] = {
        Entities.Sport.value: SportModel,
        Entities.Event.value: EventModel,
        Entities.Selection.value: SelectionModel,
    }

    @classmethod
    def create(cls, model: str) -> BaseModel:
        if model in cls._models:
            return cls._models[model]()
        raise KeyError(model)
