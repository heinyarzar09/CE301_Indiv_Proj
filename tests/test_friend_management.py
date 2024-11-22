# File: tests/test_friend_management.py

import pytest
from app import db
from app.models import User, Friendship
from flask_login import login_user

@pytest.fixture
def setup_users_and_friendships(app):
    with app.app_context():
        # Create users
        user1 = User(username='user1', email='user1@example.com', password='hashed_password')
        user2 = User(username='user2', email='user2@example.com', password='hashed_password')
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create an accepted friendship
        friendship = Friendship(user_id=user1.id, friend_id=user2.id, status='accepted')
        db.session.add(friendship)
        db.session.commit()

        yield user1, user2, friendship


def test_unfollow_friend(client, setup_users_and_friendships):
    user1, user2, friendship = setup_users_and_friendships

    # Simulate a logged-in session for user1
    with client.session_transaction() as session:
        session['_user_id'] = str(user1.id)

    # Send POST request to unfollow friend
    response = client.post(f'/unfollow_friend/{user2.id}', follow_redirects=True)
    assert response.status_code == 200

    # Check if the friendship is deleted
    deleted_friendship = Friendship.query.get(friendship.id)
    assert deleted_friendship is None


def test_block_friend(client, setup_users_and_friendships):
    user1, user2, friendship = setup_users_and_friendships

    # Simulate a logged-in session for user1
    with client.session_transaction() as session:
        session['_user_id'] = str(user1.id)

    # Send POST request to block friend
    response = client.post(f'/block_friend/{user2.id}', follow_redirects=True)
    assert response.status_code == 200

    # Check if a new block entry was created
    deleted_friendship = Friendship.query.get(friendship.id)
    new_block_entry = Friendship.query.filter_by(user_id=user1.id, friend_id=user2.id, is_blocked=True).first()
    assert new_block_entry is not None
    assert new_block_entry.status == 'blocked'


def test_unblock_friend(client, setup_users_and_friendships):
    user1, user2, _ = setup_users_and_friendships

    # Create a block entry
    block_entry = Friendship(user_id=user1.id, friend_id=user2.id, is_blocked=True, status='blocked')
    db.session.add(block_entry)
    db.session.commit()

    # Simulate a logged-in session for user1
    with client.session_transaction() as session:
        session['_user_id'] = str(user1.id)

    # Send POST request to unblock friend
    response = client.post(f'/unblock_friend/{user2.id}', follow_redirects=True)
    assert response.status_code == 200

    # Check if the block entry is deleted
    deleted_block_entry = Friendship.query.get(block_entry.id)
    assert deleted_block_entry is None


def test_manage_friends(client, setup_users_and_friendships):
    user1, user2, _ = setup_users_and_friendships

    # Simulate a logged-in session for user1
    with client.session_transaction() as session:
        session['_user_id'] = str(user1.id)

    # Send GET request to manage friends page
    response = client.get('/manage_friends')
    assert response.status_code == 200
    assert b'user2' in response.data  # Check if user2's name appears on the page
