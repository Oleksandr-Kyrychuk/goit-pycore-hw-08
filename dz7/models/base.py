from sqlalchemy.ext.declarative import declarative_base
from config import engine

Base = declarative_base()
Base.metadata.bind = engine