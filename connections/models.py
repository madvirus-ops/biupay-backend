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
from .database import AbstractModel, TZ, get_env,uuid

tz = TZ


class Users(AbstractModel):
    __tablename__ = "users"
    user_id = Column(String(255), default=uuid.uuid4, nullable=False, unique=True, index=True)
    full_name = Column(String(255), default="")

    email = Column(String(255), nullable=True)
    phone_number = Column(String(255), default="")
    department = Column(String(255), default="")
    last_login = Column(DateTime, default=datetime.now(TZ))
    is_active = Column(Boolean, default=False)
    matric_number = Column(String(255), default="")
    level = Column(String(255), default="")


    
class Departments(AbstractModel):
    __tablename__ = "departments"
    code = Column(String(255), default="")
    name = Column(String(255), default="")
    account_number = Column(String(255), default="")
    dues_amount = Column(Numeric,default=0.0)
    payment_fees = Column(Numeric,default=0.0)
    bank_code = Column(String(255), default="51204") #above only


class Transactions(AbstractModel):
    __tablename__ = "transactions"
    payer_email = Column(String(255), default="")
    status = Column(String(255), default="pending")  # pending or processed when the webhook neva come
    payment_status = Column(String(255), default="") #completed or processing.
    department_code = Column(String(255), default="")
    payment_reference = Column(String(255), default="")
    amount = Column(Numeric, default=0.0)
    session = Column(String(255), default="2023/2024")
    level = Column(String(255),default="100")


class PaystackWebhooks(AbstractModel):
    __tablename__ = "paystack_reference"
    payer_email = Column(String(255), default="")
    reference = Column(String(255), default="active")
    body = Column(Text, nullable=True)
    status = Column(String(255), default="pending") 

