import pytest
import tempfile
from backend import app, db

@pytest.fixture(scope='function')
def client(tmp_path, monkeypatch):
    # Use a temporary sqlite file for isolation
    db_file = tmp_path / "test_db.sqlite"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_file.as_posix()}"
    app.config['TESTING'] = True
    # Recreate schema
    with app.app_context():
        try:
            db.drop_all()
        except Exception:
            pass
        db.create_all()
    client = app.test_client()
    yield client
    # teardown happens via tmp_path cleanup
