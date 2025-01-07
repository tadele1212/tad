import pytest
from ..db import DatabaseConnection

@pytest.fixture
def db_connection():
    return DatabaseConnection()

def test_database_connection(db_connection):
    with db_connection.get_cursor() as cursor:
        assert cursor is not None
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result is not None
        assert result["1"] == 1

def test_show_stop_procedure(db_connection):
    with db_connection.get_cursor() as cursor:
        cursor.callproc('Show_Stop', ["163-1"])
        results = next(cursor.stored_results())
        stops = results.fetchall()
        assert len(stops) > 0
        assert "sequence" in stops[0]
        assert "road_name" in stops[0]
        assert "km" in stops[0] 