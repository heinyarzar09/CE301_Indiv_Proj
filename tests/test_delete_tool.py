import pytest
from app import create_app, db
from app.models import User, Tool
from flask_login import login_user

# Fixture to set up the app in testing mode
@pytest.fixture
def app():
    app = create_app()  # Use your create_app() function
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
def client(app):
    return app.test_client()

@pytest.fixture
def setup_user(app):
    # Set up a test user
    user = User(username='testuser', email='test@example.com', password='hashed_password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def setup_tool(app, setup_user):
    # Set up a test tool for the user
    tool = Tool(name='Measuring Cup', unit='ml', owner_id=setup_user.id)
    db.session.add(tool)
    db.session.commit()
    return tool

def test_delete_tool_success(client, setup_user, setup_tool):
    """Test deleting a tool successfully."""
    user = setup_user
    tool = setup_tool

    # Log in the user using Flask-Login
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Make a POST request to delete the tool
        response = client.post(f'/delete_tool/{tool.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b"Tool has been deleted." in response.data
        # Check if the tool has been deleted from the database
        assert Tool.query.get(tool.id) is None

def test_delete_tool_forbidden(client, setup_user, setup_tool):
    """Test deleting a tool that doesn't belong to the user (should return 403 Forbidden)."""
    # Create a second user who does not own the tool
    second_user = User(username='otheruser', email='other@example.com', password='hashed_password')
    db.session.add(second_user)
    db.session.commit()

    # Log in the second user
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(second_user.id)  # Mock the second user's session

        # Attempt to delete the tool owned by the first user
        response = client.post(f'/delete_tool/{setup_tool.id}', follow_redirects=True)
        assert response.status_code == 403  # Forbidden

def test_delete_tool_not_found(client, setup_user):
    """Test deleting a tool that does not exist (should return 404 Not Found)."""
    user = setup_user

    # Log in the user using Flask-Login
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Attempt to delete a non-existent tool
        response = client.post('/delete_tool/9999', follow_redirects=True)  # Use an ID that does not exist
        assert response.status_code == 404  # Not Found
