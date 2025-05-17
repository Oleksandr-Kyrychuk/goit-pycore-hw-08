from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///dz7.db"
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)