import pytest, os
from inf349 import create_app
from inf349.models import db, create_tables

@pytest.fixture
def client(tmp_path):
    app = create_app()
    app.config.update(
        DATABASE = tmp_path / "test.db",
        TESTING = True,
    )
    db.init(app.config["DATABASE"])
    create_tables()
    with app.test_client() as client:
        yield client
