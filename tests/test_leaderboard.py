# File: tests/test_leaderboard.py

import pytest
from app.models import Challenge, ChallengeParticipant, Achievement, User
from app import db
from datetime import datetime, timedelta, timezone

from app.user_routes import end_challenge, get_challenge_winner

@pytest.fixture
def setup_challenges(app):
    with app.app_context():
        # Create test users
        user1 = User(username='user1', email='user1@example.com', password='hashed_password', credits=0)
        user2 = User(username='user2', email='user2@example.com', password='hashed_password', credits=0)
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create an active challenge
        challenge1 = Challenge(
            name='Active Challenge',
            icon='challenge1.png',
            creator_id=user1.id,
            credits_required=50,
            duration=86400,  # 1 day in seconds
            started_at=datetime.now(timezone.utc) - timedelta(hours=12)  # Started 12 hours ago
        )
        db.session.add(challenge1)
        db.session.commit()

        # Add participants
        participant1 = ChallengeParticipant(user_id=user1.id, challenge_id=challenge1.id, progress=80, wagered_credits=30)
        participant2 = ChallengeParticipant(user_id=user2.id, challenge_id=challenge1.id, progress=100, wagered_credits=20)
        db.session.add_all([participant1, participant2])
        db.session.commit()

        # Create an ended challenge
        challenge2 = Challenge(
            name='Ended Challenge',
            icon='challenge2.png',
            creator_id=user2.id,
            credits_required=100,
            duration=86400,  # 1 day
            started_at=datetime.now(timezone.utc) - timedelta(days=2)  # Ended 1 day ago
        )
        challenge2.ended = True
        db.session.add(challenge2)
        db.session.commit()

        yield [challenge1, challenge2], [participant1, participant2]

def test_leaderboard(client, setup_challenges):
    challenges, participants = setup_challenges
    challenge1, challenge2 = challenges

    # Simulate a logged-in session
    with client.session_transaction() as session:
        session['_user_id'] = str(participants[0].user_id)

    # Send GET request to the leaderboard route
    response = client.get('/leaderboard')
    assert response.status_code == 200

    # Check that only the active challenge is displayed
    assert b'Active Challenge' in response.data
    assert b'Ended Challenge' not in response.data

    # Check that participants are sorted by progress in descending order
    assert b'user2' in response.data  # user2 (progress=100) should appear before user1 (progress=80)

def test_get_challenge_winner(setup_challenges):
    challenges, participants = setup_challenges
    challenge1, challenge2 = challenges

    # Test for an active challenge
    winner = get_challenge_winner(challenge1)
    assert winner.user_id == participants[1].user_id  # user2 should be the winner

    # Test for an ended challenge
    winner = get_challenge_winner(challenge2)
    assert winner is None  # No participants in the ended challenge

