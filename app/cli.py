from datetime import datetime
from typing import Any, Dict, List, Optional

import typer

from app.enums import Entities, Operators, OutcomeEnum, StatusEnum, TypeEnum
from app.models import ModelFactory
from app.schemas import SchemaFactory

NULL_FOREIGN_KEY = 0

app = typer.Typer()


def _create(entity: str, **kwargs) -> None:
    schema = SchemaFactory.create(entity, **kwargs)
    model = ModelFactory.create(entity)

    schema = model.insert(schema)
    typer.echo(
        f'Inserted {entity.capitalize()} with ID: {schema.get_id()} successfully.'
    )


def _update(entity: str, id: int, arguments: Dict[str, Any]) -> None:
    if all(value == None for value in arguments.values()):
        typer.echo('Nothing was requested to be changed.')
        return
    new_schema = {k: v for k, v in arguments.items() if v != None}

    model = ModelFactory.create(entity)
    old_model = model.find(id)

    model_dict = old_model.dict()
    model_dict.update(new_schema)

    updated_model = SchemaFactory.create(entity, **model_dict)

    model.update(updated_model)

    typer.echo(f'Updated {entity.capitalize()} with ID: {id} successfully.')


@app.command()
def create_sport(
    name: str,
    slug: str,
    active: Optional[bool] = typer.Option(True, '--active/--inactive'),
) -> None:
    _create(Entities.Sport.value, **{'Name': name, 'Slug': slug, 'Active': active})


@app.command()
def create_event(
    name: str,
    slug: str,
    type: TypeEnum,
    status: StatusEnum,
    scheduled_start: datetime,
    sport: Optional[int] = NULL_FOREIGN_KEY,  # Typer doesn't support NewType yet.
    active: Optional[bool] = typer.Option(True, '--active/--inactive'),
) -> None:
    _create(
        Entities.Event.value,
        **{
            'Name': name,
            'Slug': slug,
            'Active': active,
            'Type': type,
            'Sport': sport,
            'Status': status,
            'ScheduledStart': scheduled_start,
        },
    )


@app.command()
def create_selection(
    name: str,
    price: float,
    outcome: OutcomeEnum,
    event: int = NULL_FOREIGN_KEY,  # Typer doesn't support NewType yet.
    active: Optional[bool] = typer.Option(True, '--active/--inactive'),
) -> None:
    _create(
        Entities.Selection.value,
        **{
            'Name': name,
            'Event': event,
            'Price': price,
            'Active': active,
            'Outcome': outcome,
        },
    )


@app.command()
def search(entity: str, select_field: List[str] = typer.Option(default=[])) -> None:
    model = ModelFactory.create(entity)

    if select_field:
        model.select(*select_field)
    while True:
        field = typer.prompt('Field to filter via')

        operators = Operators.get_operators()
        while True:
            operator = typer.prompt(
                f"Operator({', '.join(op for op in operators.keys())}) to filter via"
            )
            if operator in operators:
                operator = operators[operator]
                break
        value = typer.prompt('Value to filter via')

        model.filter(field, operator, value)

        cont = typer.confirm('Would you like to add another filter')
        if not cont:
            break
    result = model.execute()

    result_str = f"Found: {result} successfully." if result else "Nothing was found."
    typer.echo(result_str)

@app.command()
def update_sport(
    id: int,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    active: Optional[bool] = typer.Option(None, '--active/--inactive'),
) -> None:
    _update(Entities.Sport.value, id, {'Name': name, 'Slug': slug, 'Active': active})


@app.command()
def update_event(
    id: int,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    active: Optional[bool] = typer.Option(None, '--active/--inactive'),
    type: Optional[TypeEnum] = None,
    status: Optional[StatusEnum] = None,
    scheduled_start: Optional[datetime] = None,
    sport: Optional[int] = None,
) -> None:
    _update(
        Entities.Event.value,
        id,
        {
            'Name': name,
            'Slug': slug,
            'Active': active,
            'Type': type,
            'Status': status,
            'ScheduledStart': scheduled_start,
            'Sport': sport,
        },
    )


@app.command()
def update_selection(
    id: int,
    name: Optional[str] = None,
    price: Optional[float] = None,
    active: Optional[bool] = typer.Option(None, '--active/--inactive'),
    outcome: Optional[OutcomeEnum] = None,
    event: Optional[int] = None,
) -> None:
    _update(
        Entities.Selection.value,
        id,
        {
            'Name': name,
            'Price': price,
            'Active': active,
            'Outcome': outcome,
            'Event': event,
        },
    )

def main() -> None:
    app()