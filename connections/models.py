import sys

sys.path.append("./")
from sqlalchemy import (
    Column,
    DateTime,
    Boolean,
    Integer,
    String,
    Text,
    Numeric,
    ForeignKey,
    Date,
    asc,
    desc,
    func,
)
from datetime import datetime
from sqlalchemy.orm import relationship
from .database import AbstractModel, TZ, get_env

tz = TZ


class Users(AbstractModel):
    __tablename__ = "users"
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(255), default="")
    last_name = Column(String(255), default="")
    username = Column(String(255), default="")

    email = Column(String(255), nullable=True)
    password = Column(String(255), default="")
    phone_number = Column(String(255), default="")

    last_login = Column(DateTime, default=datetime.now(TZ))
    is_active = Column(Boolean, default=False)

    