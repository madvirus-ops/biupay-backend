import sys

sys.path.append("./")
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)
import uuid
import pytz
from datetime import datetime
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()


def get_env(value: str):
    return os.getenv(value)



SQLALCHEMY_DATABASE_URL = get_env("SQLALCHEMY_DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=50,
    max_overflow=20,
    # pool_timeout=120,
    # pool_recycle=900,
    # pool_pre_ping=True,
    # connect_args={"options": "-c idle_in_transaction_session_timeout=20000"},
)
Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    ensures the database connection is always closed
    to use this we have to use fastapi.Depends() as an argument in the routes
    """
    db = SessionLocal()
    try:
        yield db

    except Exception as e:
        print(e.args)
        db.rollback()

    finally:
        db.close()


logger = logging.getLogger(__name__)


TZ = pytz.timezone("Africa/Lagos")





class AbstractModel(Base):
    """abstract model"""

    __abstract__ = True
    pkid = Column(Integer, primary_key=True)
    id = Column(String(255), default=uuid.uuid4, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now(TZ))
    updated_at = Column(DateTime, default=datetime.now(TZ))
