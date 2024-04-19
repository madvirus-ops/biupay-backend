import sys
sys.path.append("./")
from pydantic import BaseModel



class InitPayment(BaseModel):
    email: str
    full_name: str
    phone_number: str
    department_code: str
    level: str
    matric_number: str
    session: str