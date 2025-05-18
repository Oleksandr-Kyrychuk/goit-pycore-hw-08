# repository.py
from sqlalchemy.orm import Session
from main import User, Contact, get_password_hash


class UserRepository:
    """Repository for user-related database operations."""

    @staticmethod
    def create_user(db: Session, email: str, password: str, verification_token: str):
        """Create a new user in the database.

        Args:
            db (Session): Database session.
            email (str): User email.
            password (str): Plain text password to hash.
            verification_token (str): Verification token for email.

        Returns:
            User: The created user object.
        """
        hashed_password = get_password_hash(password)
        db_user = User(email=email, hashed_password=hashed_password, verification_token=verification_token)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """Retrieve a user by email.

        Args:
            db (Session): Database session.
            email (str): User email.

        Returns:
            User: The user object or None if not found.
        """
        return db.query(User).filter(User.email == email).first()


class ContactRepository:
    """Repository for contact-related database operations."""

    @staticmethod
    def create_contact(db: Session, contact_data: dict, user_id: int):
        """Create a new contact for a user.

        Args:
            db (Session): Database session.
            contact_data (dict): Contact data (first_name, last_name, etc.).
            user_id (int): ID of the user owning the contact.

        Returns:
            Contact: The created contact object.
        """
        db_contact = Contact(**contact_data, user_id=user_id)
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact