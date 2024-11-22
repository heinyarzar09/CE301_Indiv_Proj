import pytest
from app import create_app, db

# Fixture to set up the app in testing mode
@pytest.fixture
def app():
    app = create_app()  # Removed the 'testing' argument since it doesn't exist
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    with app.app_context():
        db.create_all()  # Create the tables
        yield app
        db.session.remove()
        db.drop_all()  # Clean up

# Fixture for the test client
@pytest.fixture
def test_manual_conversion_tool_get(client):
    """Test accessing the manual conversion tool page."""
    response = client.get('/manual_conversion_tool')
    assert response.status_code == 200

def test_manual_conversion_tool_post_valid(client):
    """Test a valid conversion submission."""
    response = client.post('/manual_conversion_tool', data={
        'amount': '1',
        'from_unit': 'cup',
        'to_unit': 'tablespoon'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_manual_conversion_tool_post_invalid(client):
    """Test an invalid conversion submission."""
    response = client.post('/manual_conversion_tool', data={
        'amount': '1',
        'from_unit': 'invalid_unit',
        'to_unit': 'tablespoon'
    }, follow_redirects=True)
    assert response.status_code == 200
