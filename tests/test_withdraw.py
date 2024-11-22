import pytest
from app import db
from app.models import User, CreditWithdrawRequest
from flask import url_for


@pytest.fixture
def setup_user_with_credits(app):
    """Fixture to set up a user with predefined credits."""
    with app.app_context():
        user = User(username='test_user', email='test_user@example.com', password='hashed_password', credits=200)
        db.session.add(user)
        db.session.commit()
        return user.id  # Return the user ID instead of the instance


def fetch_user(user_id):
    """Fetch the user by ID within the session."""
    return User.query.get(user_id)


def simulate_login(client, user_id):
    """Simulate a logged-in session for a user."""
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)



def test_request_withdraw_insufficient_credits(client, setup_user_with_credits, app):
    user_id = setup_user_with_credits
    simulate_login(client, user_id)

    with app.test_request_context():
        url = url_for('user.request_withdraw')

    response = client.post(
        url,
        data={
            'credits_requested': 300,  # More than available credits
            'payment_mode': 'Bank Transfer',
            'phone_number': '1234567890'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    # Additional database verification
    with app.app_context():
        assert CreditWithdrawRequest.query.filter_by(user_id=user_id).count() == 0



def test_track_withdraw(client, setup_user_with_credits, app):
    user_id = setup_user_with_credits
    simulate_login(client, user_id)

    with app.app_context():
        # Add withdrawal requests to the database
        user = fetch_user(user_id)
        withdraw_request1 = CreditWithdrawRequest(user_id=user.id, credits_requested=50, payment_mode='Bank Transfer', phone_number='1234567890')
        withdraw_request2 = CreditWithdrawRequest(user_id=user.id, credits_requested=100, payment_mode='PayPal', phone_number='9876543210')
        db.session.add_all([withdraw_request1, withdraw_request2])
        db.session.commit()

    with app.test_request_context():
        url = url_for('user.track_withdraw')

    response = client.get(url)
    assert response.status_code == 200
    assert b'50' in response.data
    assert b'100' in response.data


def test_track_withdraw_empty(client, setup_user_with_credits, app):
    user_id = setup_user_with_credits
    simulate_login(client, user_id)

    with app.test_request_context():
        url = url_for('user.track_withdraw')

    response = client.get(url)
    assert response.status_code == 200
    assert b'No withdrawal requests found.' in response.data
