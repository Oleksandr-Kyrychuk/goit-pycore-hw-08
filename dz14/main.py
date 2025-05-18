import os
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import uvicorn
from redis.asyncio import Redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import cloudinary
import cloudinary.uploader
from fastapi import File, UploadFile
from repository import UserRepository, ContactRepository

app = FastAPI(
    title="Contacts API",
    description="REST API for managing user contacts with authentication, email verification, and avatar upload."
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DB setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- JWT settings ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# --- SMTP settings ---
EMAIL_FROM = os.getenv("EMAIL_FROM")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# --- Cloudinary setup ---
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# --- Redis setup ---
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL not set in .env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# --- Models ---
class User(Base):
    """Database model for users."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)


class Contact(Base):
    """Database model for contacts."""
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    birthday = Column(Date, nullable=False)
    additional_data = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


# --- Schemas ---
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    verified: bool
    avatar_url: Optional[str]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: datetime
    additional_data: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int

    class Config:
        orm_mode = True


# --- Create tables ---
Base.metadata.create_all(bind=engine)


# --- Dependency ---
def get_db():
    """Provide a database session.

    Yields:
        Session: SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Redis initialization ---
@app.on_event("startup")
async def startup_event():
    """Initialize Redis for rate limiting and caching on application startup."""
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    await FastAPILimiter.init(redis)


# --- Email sending utility ---
def send_email(to_email: str, subject: str, body: str):
    """Send an email using SMTP.

    Args:
        to_email (str): Recipient email address.
        subject (str): Email subject.
        body (str): Email body content.

    Raises:
        SMTPException: If email sending fails.
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, to_email, msg.as_string())


# --- Auth utils ---
def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    """Create a JWT access token.

    Args:
        data (dict): Data to encode in the token (e.g., user ID).

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """Create a JWT refresh token.

    Args:
        data (dict): Data to encode in the token (e.g., user ID).

    Returns:
        str: The encoded JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Retrieve the current authenticated user.

    Args:
        token (str): JWT token from the Authorization header.
        db (Session): Database session dependency.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException: If credentials are invalid or email is not verified.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Check Redis cache
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    cached_user = await redis.get(f"user:{user_id}")
    if cached_user:
        import json
        user_data = json.loads(cached_user)
        user = User(**user_data)
    else:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        # Cache user data
        await redis.setex(f"user:{user_id}", 3600, json.dumps({
            "id": user.id,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "verified": user.verified,
            "avatar_url": user.avatar_url
        }))

    if not user.verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return user


# --- Routes ---
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and send a verification email.

    Args:
        user (UserCreate): User data including email and password.
        db (Session): Database session dependency.

    Returns:
        UserResponse: The created user data.

    Raises:
        HTTPException: If the email is already registered.
    """
    db_user = UserRepository.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    verification_token = str(uuid.uuid4())
    db_user = UserRepository.create_user(db, user.email, user.password, verification_token)

    verification_url = f"http://localhost:8000/auth/verify?token={verification_token}"
    body = f"Please verify your email by clicking this link: {verification_url}"
    send_email(user.email, "Verify Your Email", body)

    return db_user


@app.get("/auth/verify")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify a user's email using a verification token.

    Args:
        token (str): The verification token sent to the user's email.
        db (Session): Database session dependency.

    Returns:
        dict: A message indicating successful verification.

    Raises:
        HTTPException: If the token is invalid or the email is already verified.
    """
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    if user.verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    user.verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully"}


@app.post("/auth/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a user and return access and refresh tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): User credentials (email and password).
        db (Session): Database session dependency.

    Returns:
        Token: Access and refresh tokens with token type.

    Raises:
        HTTPException: If credentials are incorrect.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/contacts/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    """Create a new contact for the authenticated user.

    Args:
        contact (ContactCreate): Contact data to create.
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        ContactResponse: The created contact data.
    """
    db_contact = ContactRepository.create_contact(db, contact.dict(), current_user.id)
    return db_contact


@app.get("/contacts/", response_model=List[ContactResponse])
async def get_contacts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve all contacts for the authenticated user.

    Args:
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        List[ContactResponse]: List of contacts.
    """
    return db.query(Contact).filter(Contact.user_id == current_user.id).all()


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve a specific contact by ID.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        ContactResponse: The contact data.

    Raises:
        HTTPException: If the contact is not found.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    """Update a specific contact by ID.

    Args:
        contact_id (int): The ID of the contact to update.
        contact (ContactUpdate): Updated contact data.
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        ContactResponse: The updated contact data.

    Raises:
        HTTPException: If the contact is not found.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    """Delete a specific contact by ID.

    Args:
        contact_id (int): The ID of the contact to delete.
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        dict: A message indicating successful deletion.

    Raises:
        HTTPException: If the contact is not found.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}


@app.get("/contacts/search/", response_model=List[ContactResponse])
async def search_contacts(q: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Search contacts by name or email.

    Args:
        q (str): Search query for first name, last name, or email.
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        List[ContactResponse]: List of matching contacts.
    """
    contacts = db.query(Contact).filter(
        (Contact.first_name.ilike(f"%{q}%")) |
        (Contact.last_name.ilike(f"%{q}%")) |
        (Contact.email.ilike(f"%{q}%")),
        Contact.user_id == current_user.id
    ).all()
    return contacts


@app.get("/contacts/birthdays/", response_model=List[ContactResponse])
async def get_upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve contacts with upcoming birthdays within the next 7 days.

    Args:
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        List[ContactResponse]: List of contacts with upcoming birthdays.
    """
    today = datetime.now().date()
    week_later = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        Contact.birthday >= today,
        Contact.birthday <= week_later,
        Contact.user_id == current_user.id
    ).all()
    return contacts


@app.post("/auth/password-reset-request")
async def password_reset_request(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset by sending a reset link to the user's email.

    Args:
        request (PasswordResetRequest): The email of the user requesting a reset.
        db (Session): Database session dependency.

    Returns:
        dict: A message indicating the reset email was sent.

    Raises:
        HTTPException: If the user is not found.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reset_token = str(uuid.uuid4())
    user.verification_token = reset_token
    db.commit()

    reset_url = f"http://localhost:8000/auth/password-reset?token={reset_token}"
    body = f"Reset your password by clicking this link: {reset_url}"
    send_email(user.email, "Password Reset Request", body)

    return {"message": "Password reset email sent"}


@app.post("/auth/password-reset")
async def password_reset(reset: PasswordReset, db: Session = Depends(get_db)):
    """Reset a user's password using a reset token.

    Args:
        reset (PasswordReset): The reset token and new password.
        db (Session): Database session dependency.

    Returns:
        dict: A message indicating successful password reset.

    Raises:
        HTTPException: If the reset token is invalid.
    """
    user = db.query(User).filter(User.verification_token == reset.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    user.hashed_password = get_password_hash(reset.new_password)
    user.verification_token = None
    db.commit()
    return {"message": "Password reset successfully"}


@app.post("/users/avatar", response_model=UserResponse)
async def update_avatar(file: UploadFile = File(...), db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    """Update the authenticated user's avatar using Cloudinary.

    Args:
        file (UploadFile): The image file to upload as the avatar.
        db (Session): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        UserResponse: The updated user data with the new avatar URL.
    """
    upload_result = cloudinary.uploader.upload(file.file, folder="avatars")
    current_user.avatar_url = upload_result["secure_url"]
    db.commit()
    db.refresh(current_user)
    return current_user


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)