import pytest
from typer.testing import CliRunner, Result

from app.cli import app
from typing import List

runner = CliRunner()

@pytest.mark.parametrize("arguments, entity_name", 
    [
        (['create-sport', 'testing', 'test', '--active'], 'Sport'),
        (['create-event', 'testing', 'test', 'Preplay', 'Pending', '2020-01-01T00:00:00', '--sport', '1', '--inactive'], 'Event'),
        (['create-selection', 'testing', '10.11', 'Void', '--event', '1', '--active'], 'Selection'),
    ]
)
def test_create(arguments: List[str], entity_name: str) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 0
    assert f"Inserted {entity_name} with ID: 2 successfully." in result.stdout

@pytest.mark.parametrize("arguments, entity_name", 
    [
        (['update-sport', '1', '--name', 'updated', '--slug', 'up'], 'Sport'),
        (['update-event', '1', '--name', 'updated', '--inactive'], 'Event'),
        (['update-selection', '1', '--name', 'updated', '--inactive'], 'Selection'),
    ]
)
def test_update(arguments: List[str], entity_name: str) -> None:
    # Could implement into test_create but I did it this way for increased readability.
    result = runner.invoke(app, arguments)
    
    print(result.stdout)
    assert result.exit_code == 0
    assert f"Updated {entity_name} with ID: 1 successfully." in result.stdout


def test_search() -> None:
    """Manually tested its difficult with while loops. I could refactor but I'm happy with it for now."""
    ...

