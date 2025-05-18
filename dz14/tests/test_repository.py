# tests/test_repository.py
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, User, get_password_hash
from repository import UserRepository, ContactRepository
from datetime import datetime

class TestUserRepository(unittest.TestCase):
    def setUp(self):
        """Set up an in-memory SQLite database for testing."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        """Clean up the database after each test."""
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_create_user(self):
        """Test creating a user."""
        user = UserRepository.create_user(self.db, "test@example.com", "password123", "token123")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.verification_token, "token123")
        self.assertFalse(user.verified)

    def test_get_user_by_email(self):
        """Test retrieving a user by email."""
        UserRepository.create_user(self.db, "test@example.com", "password123", "token123")
        user = UserRepository.get_user_by_email(self.db, "test@example.com")
        self.assertEqual(user.email, "test@example.com")
        user = UserRepository.get_user_by_email(self.db, "nonexistent@example.com")
        self.assertIsNone(user)

class TestContactRepository(unittest.TestCase):
    def setUp(self):
        """Set up an in-memory SQLite database for testing."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        # Create a test user
        self.user = User(email="user@example.com", hashed_password=get_password_hash("password123"))
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        """Clean up the database after each test."""
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_create_contact(self):
        """Test creating a contact."""
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone_number": "1234567890",
            "birthday": datetime.now().date(),
        }
        contact = ContactRepository.create_contact(self.db, contact_data, self.user.id)
        self.assertEqual(contact.first_name, "John")
        self.assertEqual(contact.user_id, self.user.id)

if __name__ == "__main__":
    unittest.main()