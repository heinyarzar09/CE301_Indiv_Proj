# File: tests/test_friend_requests.py

import pytest
from app import db
from app.models import User, Friendship
from flask_login import login_user


@pytest.fixture
def setup_users_and_requests(app):
    with app.app_context():
        # Create two users
        user1 = User(username='user1', email='user1@example.com', password='hashed_password')
        user2 = User(username='user2', email='user2@example.com', password='hashed_password')
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create a pending friend request from user2 to user1
        friend_request = Friendship(user_id=user2.id, friend_id=user1.id, status='pending')
        db.session.add(friend_request)
        db.session.commit()

        yield user1, user2, friend_request


def test_approve_friend_request(client, setup_users_and_requests):
    user1, user2, friend_request = setup_users_and_requests

    # Simulate a logged-in session for user1
    with client.session_transaction() as session:
        session['_user_id'] = str(user1.id)

    # Send POST request to approve the friend request
    response = client.post(f'/approve_friend_request/{friend_request.id}', follow_redirects=True)
    assert response.status_code == 200

    # Check if the status is updated to 'accepted'
    updated_request = Friendship.query.get(friend_request.id)
    assert updated_request.status == 'accepted'


def test_reject_friend_request(client, setup_users_and_requests):
    user1, user2, friend_request = setup_users_and_requests

    # Simulate a logged-in session for user1
    with client.session_transaction() as session:
        session['_user_id'] = str(user1.id)

    # Send POST request to reject the friend request
    response = client.post(f'/reject_friend_request/{friend_request.id}', follow_redirects=True)
    assert response.status_code == 200

    # Check if the request is deleted
    deleted_request = Friendship.query.get(friend_request.id)
    assert deleted_request is None


def test_send_friend_request(client, setup_users_and_requests):
    user1, user2, _ = setup_users_and_requests

    # Simulate a logged-in session for user1
    with client.session_transaction() as session:
        session['_user_id'] = str(user1.id)

    # Send POST request to send a new friend request
    response = client.post(f'/send_friend_request/{user2.id}', follow_redirects=True)
    assert response.status_code == 200

    # Check if a new request has been created
    new_request = Friendship.query.filter_by(user_id=user1.id, friend_id=user2.id).first()
    assert new_request is not None
    assert new_request.status == 'pending'

