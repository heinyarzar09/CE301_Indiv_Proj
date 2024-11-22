# tests/test_register.py
import unittest
from app import create_app, db
from flask import url_for

class TestRegister(unittest.TestCase):

    def setUp(self):
        # Setup the Flask app and create a test client
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        # Initialize the database
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        # Clean up the database
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register_user(self):
        # Make a POST request to the registration route
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'role': 'user'
        }, follow_redirects=True)

        # Check if the registration was successful
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your account has been created!', response.data)

if __name__ == '__main__':
    unittest.main()
