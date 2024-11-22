import pytest
from app import create_app, db

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"  # Use an in-memory database for testing
    })

    with app.app_context():
        db.create_all()  # Create all database tables
        yield app
        db.session.remove()
        db.drop_all()  # Drop all tables after testing

@pytest.fixture
def client(app):
    return app.test_client()
