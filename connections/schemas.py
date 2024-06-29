import sys
sys.path.append("./")
from pydantic import BaseModel,PositiveFloat
from typing import Optional



class InitPayment(BaseModel):
    email: str
    full_name: str
    phone_number: str
    department_code: str
    level: str
    matric_number: str
    session: str



class DepartmentsIN(BaseModel):
    id:str
    code: Optional[str] = None
    name: Optional[str] = None
    account_number: Optional[str] = None
    dues_amount: Optional[PositiveFloat] = None
    payment_fees: Optional[PositiveFloat] = None
    bank_code: Optional[str] = "51204"
