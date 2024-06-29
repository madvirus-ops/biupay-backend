import sys

sys.path.append("./")
from connections.database import get_db
from controllers.admin import listAllBanks,edit_department
from fastapi import APIRouter, Response, Request, Depends
from sqlalchemy.orm import Session
from connections.schemas import DepartmentsIN


router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])



@router.put("/edit")
async def departments(
    body: DepartmentsIN, response: Response, db: Session = Depends(get_db)
):
    result = edit_department(
        body,
        db
    )
    response.status_code = result["code"]
    return result



@router.get("/banks")
async def banks(db: Session = Depends(get_db)):
    return listAllBanks()